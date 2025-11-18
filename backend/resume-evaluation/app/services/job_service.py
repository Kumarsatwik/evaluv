from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional, List
from uuid import UUID
from ..models.job import Job
from ..schemas.job import JobCreateRequest, JobUpdateRequest
from ..utils.exceptions import NotFoundException


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

    async def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        statement = select(Job)
        result = await self.session.exec(statement)
        return list(result.all())

    async def create_job(self, job_create: JobCreateRequest, created_by: UUID) -> Job:
        """Create a new job"""
        data = job_create.model_dump()
        data['created_by'] = created_by
        db_job = Job(**data)
        self.session.add(db_job)
        await self.session.commit()
        await self.session.refresh(db_job)
        return db_job

    async def update_job(self, job_id: UUID, job_update: JobUpdateRequest, created_by: UUID) -> Optional[Job]:
        """Update job information (only by creator)"""
        db_job = await self.get_job_by_id(job_id)
        if not db_job or str(db_job.created_by) != str(created_by):
            raise NotFoundException("Job not found or access denied")

        update_data = job_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job, field, value)

        await self.session.commit()
        await self.session.refresh(db_job)
        return db_job

    async def delete_job(self, job_id: UUID, created_by: UUID) -> bool:
        """Delete job (only by creator or admin)"""
        db_job = await self.get_job_by_id(job_id)
        if not db_job or str(db_job.created_by) != str(created_by):
            raise NotFoundException("Job not found or access denied")

        await self.session.delete(db_job)
        await self.session.commit()
        return True
