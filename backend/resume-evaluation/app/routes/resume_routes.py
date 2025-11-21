from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks, HTTPException
from uuid import UUID
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from ..database import get_async_session
from ..controllers.resume_controller import ResumeController
from ..models.resume import ResumeResponse

def get_resume_controller(session: AsyncSession = Depends(get_async_session)) -> ResumeController:
    """Dependency to get ResumeController instance"""
    return ResumeController(session)

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/{job_id}/upload", response_model=dict)
async def upload_resume(
    job_id: UUID,
    files: List[UploadFile] = File(...),
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    controller: ResumeController = Depends(get_resume_controller)
):
    """Upload bulk resumes for a job"""
    try:
        return await controller.upload_resumes(job_id, files, request, background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/generate_presigned_url')
async def generate_presigned_url(controller: ResumeController = Depends(get_resume_controller)):
    return await controller.generate_presigned_url()

@router.get("/job/{job_id}", response_model=List[ResumeResponse])
async def get_resumes_for_job(
    job_id: UUID,
    request: Request,
    controller: ResumeController = Depends(get_resume_controller)
):
    """Get all resumes for a specific job"""
    return await controller.get_resumes_for_job(job_id, request)

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    request: Request,
    controller: ResumeController = Depends(get_resume_controller)
):
    """Get a specific resume by ID"""
    return await controller.get_resume_by_id(resume_id, request)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    controller: ResumeController = Depends(get_resume_controller)
):
    """Delete a resume"""
    return await controller.delete_resume(resume_id, request, background_tasks)
