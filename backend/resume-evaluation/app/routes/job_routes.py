from uuid import UUID
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from fastapi import BackgroundTasks
from ..database import get_async_session
from ..controllers.job_controller import JobController
from ..schemas.job import JobResponse, JobCreateRequest, JobUpdateRequest


def get_job_controller(session: AsyncSession = Depends(get_async_session)) -> JobController:
    """Dependency to get JobController instance"""
    return JobController(session)


router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse)
async def create_job(
    job: JobCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    controller: JobController = Depends(get_job_controller)
):
    """Create a new job"""
    return await controller.create_job(job, request, background_tasks)

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_by_id(
    job_id: UUID,
    request: Request,
    controller: JobController = Depends(get_job_controller)
):
    """Get job by ID"""
    return await controller.get_job_by_id(job_id, request)

@router.get("/", response_model=List[JobResponse])
async def get_all_jobs(
    request: Request,
    controller: JobController = Depends(get_job_controller)
):
    """Get all jobs"""
    return await controller.get_all_jobs(request)

@router.get("/my/", response_model=List[JobResponse])
async def get_my_jobs(
    request: Request,
    controller: JobController = Depends(get_job_controller)
):
    """Get current user's jobs"""
    return await controller.get_my_jobs(request)

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job: JobUpdateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    controller: JobController = Depends(get_job_controller)
):
    """Update job"""
    return await controller.update_job(job_id, job, request, background_tasks)

@router.delete("/{job_id}")
async def delete_job(
    job_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,  
    controller: JobController = Depends(get_job_controller)
):
    """Delete job"""
    return await controller.delete_job(job_id, request, background_tasks)
