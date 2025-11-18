from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from uuid import UUID
from ..services.job_service import JobService
from ..schemas.job import JobResponse, JobCreateRequest, JobUpdateRequest
from ..utils.exceptions import NotFoundException
from fastapi import HTTPException, status, Request


class JobController:
    """Controller for job management operations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_service = JobService(session)

    async def create_job(self, job_create: JobCreateRequest, request: Request) -> JobResponse:
        """Create a new job"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        created_by = UUID(request.state.user["id"])
        job = await self.job_service.create_job(job_create, created_by)
        return job

    async def get_job_by_id(self, job_id: UUID, request: Request) -> JobResponse:
        """Get job by ID"""
        job = await self.job_service.get_job_by_id(job_id)
        if not job:
            raise NotFoundException("Job not found")

        return JobResponse.model_validate(job)

    async def get_my_jobs(self, request: Request) -> List[JobResponse]:
        """Get all jobs created by the current user"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        created_by = UUID(request.state.user["id"])
        jobs = await self.job_service.get_jobs_by_creator(created_by)
        return [JobResponse.model_validate(job) for job in jobs]

    async def get_all_jobs(self, request: Request) -> List[JobResponse]:
        """Get all jobs (for evaluation purposes)"""
        jobs = await self.job_service.get_all_jobs()
        return jobs

    async def update_job(self, job_id: UUID, job_update: JobUpdateRequest, request: Request) -> JobResponse:
        """Update job (only by creator)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        created_by = UUID(request.state.user["id"])
        job = await self.job_service.update_job(job_id, job_update, created_by)
        if not job:
            raise NotFoundException("Job not found or access denied")

        return job

    async def delete_job(self, job_id: UUID, request: Request) -> dict:
        """Delete job (only by creator)"""
        if not hasattr(request.state, 'user') or not request.state.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )

        created_by = UUID(request.state.user["id"])
        success = await self.job_service.delete_job(job_id, created_by)
        if not success:
            raise NotFoundException("Job not found or access denied")

        return {"message": "Job deleted successfully"}
