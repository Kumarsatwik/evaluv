from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, List
from uuid import UUID
from ..models.job import Job
from ..schemas.job import JobCreateRequest, JobUpdateRequest, JobResponse
from ..utils.exceptions import NotFoundException
from ..utils.redis_client import redis_client
from ..config import settings
from fastapi import BackgroundTasks
import json


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_job_by_id(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID"""
        statement = select(Job).where(Job.id == job_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_jobs_by_creator(self, created_by: UUID) -> List[Job]:
        """Get all jobs created by a user"""
        statement = select(Job).where(Job.created_by == created_by)
        result = await self.session.exec(statement)
        return list(result.all())

    async def get_all_jobs(self) -> List[JobResponse]:
        """Get all jobs with optional caching"""
        cached_data = await redis_client.cache_get("jobs:all")
        if cached_data:
            try:
                jobs_data = json.loads(cached_data)
                return [JobResponse(**job_data) for job_data in jobs_data]
            except json.JSONDecodeError:
                pass  # Fall back to database

        # Get from database
        jobs = await self._get_all_jobs_from_db()

        # Cache results
        if jobs:
            jobs_data = [job.model_dump() for job in jobs]
            await redis_client.cache_set("jobs:all", json.dumps(jobs_data), settings.CACHE_TTL_SECONDS)

        return jobs

    async def _get_all_jobs_from_db(self) -> List[JobResponse]:
        """Get all jobs from database"""
        statement = select(Job)
        result = await self.session.exec(statement)
        jobs = list(result.all())
        return [JobResponse.model_validate(job) for job in jobs]

    async def create_job(self, job_create: JobCreateRequest, created_by: UUID,background_tasks: BackgroundTasks) -> JobResponse:
        """Create a new job"""
        data = job_create.model_dump()
        data['created_by'] = created_by
        db_job = Job(**data)
        self.session.add(db_job)
        await self.session.commit()
        await self.session.refresh(db_job)

        from ..background.process_embedding import process_job_embedding_task
        background_tasks.add_task(process_job_embedding_task, db_job.id)

        # Invalidate cache
        await redis_client.cache_delete("jobs:all")

        return JobResponse.model_validate(db_job)

    async def update_job(self, job_id: UUID, job_update: JobUpdateRequest, created_by: UUID,background_tasks: BackgroundTasks) -> Optional[JobResponse]:
        """Update job information (only by creator)"""
        db_job = await self.get_job_by_id(job_id)
        if not db_job or str(db_job.created_by) != str(created_by):
            raise NotFoundException("Job not found or access denied")

        update_data = job_update.model_dump(exclude_unset=True)
        vector_relevant_fields = {'title', 'description', 'skills', 'experience', 'location'}
        
        # Check if any of the keys in update_data are in vector_relevant_fields
        needs_reembedding = any(field in update_data for field in vector_relevant_fields)

        for field, value in update_data.items():
            setattr(db_job, field, value)
        if needs_reembedding:
            # Mark as pending so UI knows it's processing
            db_job.embedding_status = "pending" 
            
            # Import the task here to avoid circular imports
            from ..background.process_embedding import process_job_embedding_task
            
            # Schedule the background task
            background_tasks.add_task(process_job_embedding_task, db_job.id)

        self.session.add(db_job)
        await self.session.commit()
        await self.session.refresh(db_job)
        

        # Invalidate cache
        await redis_client.cache_delete("jobs:all")

        return JobResponse.model_validate(db_job)

    async def delete_job(self, job_id: UUID, created_by: UUID,background_tasks: BackgroundTasks) -> bool:
        """Delete job (only by creator or admin)"""
        db_job = await self.get_job_by_id(job_id)
        if not db_job or str(db_job.created_by) != str(created_by):
            raise NotFoundException("Job not found or access denied")

        await self.session.delete(db_job)
        await self.session.commit()
        
        # Schedule background task to delete embeddings
        from ..background.process_embedding import delete_job_embedding_task
        background_tasks.add_task(delete_job_embedding_task, db_job.qdrant_point_id)

        # Invalidate cache
        await redis_client.cache_delete("jobs:all")

        return True
