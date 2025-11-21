from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from uuid import UUID
from fastapi import HTTPException, status, Request, BackgroundTasks
from ..services.resume_service import ResumeService
from ..models.resume import ResumeResponse
from ..utils.exceptions import NotFoundException


class ResumeController:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_service = ResumeService(session)

    async def generate_presigned_url(self):
        """Generate presigned URL for resume upload"""
        return await self.resume_service.generate_presigned_url()

    async def get_resume_by_id(self, resume_id: UUID, request: Request) -> ResumeResponse:
        """Get resume by ID"""
        resume = await self.resume_service.get_resume_by_id(resume_id)
        if not resume:
            raise NotFoundException("Resume not found")

        return ResumeResponse.model_validate(resume)

    async def get_resumes_for_job(self, job_id: UUID, request: Request) -> List[ResumeResponse]:
        """Get all resumes for a specific job"""
        return await self.resume_service.get_resumes_for_job(job_id)

    async def upload_resumes(self, job_id: UUID, files: List[dict], request: Request, background_tasks: BackgroundTasks) -> dict:
        """Upload bulk resumes for a job"""
        return await self.resume_service.upload_resumes(job_id, files, request, background_tasks)

    async def delete_resume(self, resume_id: UUID, request: Request, background_tasks: BackgroundTasks) -> dict:
        """Delete resume"""
        success = await self.resume_service.delete_resume(resume_id)
        if not success:
            raise NotFoundException("Resume not found")

        return {"message": "Resume deleted successfully"}
