import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from uuid import uuid4
from sqlmodel import select, delete
from typing import List, Optional
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, BackgroundTasks
from ..models.resume import Resume, ResumeResponse
from ..config import settings
from ..utils.exceptions import NotFoundException


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_presigned_url(self) -> dict:
        """Generate presigned URL for resume upload"""
        try:
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            # Generate unique object key
            object_key = f"resumes/{uuid4()}.pdf"

            # Generate presigned URL
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': object_key,
                    'ContentType': 'application/pdf'  # Assuming PDF format
                },
                ExpiresIn=settings.PRESIGNED_URL_EXPIRATION
            )

            return {
                "url": presigned_url,
                "key": object_key,
                "bucket": settings.S3_BUCKET_NAME
            }

        except NoCredentialsError:
            raise NotFoundException("AWS credentials not available")
        except ClientError as e:
            raise NotFoundException(f"AWS client error: {str(e)}")
        except Exception as e:
            raise NotFoundException(f"Error generating presigned URL: {str(e)}")

    async def get_resume_by_id(self, resume_id: UUID) -> Optional[Resume]:
        """Get resume by ID"""
        statement = select(Resume).where(Resume.id == resume_id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_resumes_for_job(self, job_id: UUID) -> List[ResumeResponse]:
        """Get all resumes for a specific job"""
        statement = select(Resume).where(Resume.job_id == job_id)
        result = await self.session.exec(statement)
        resumes = list(result.all())
        return [ResumeResponse.model_validate(resume) for resume in resumes]

    async def upload_resumes(self, job_id: UUID, files: List[dict], request: Request, background_tasks: BackgroundTasks) -> dict:
        """Upload and process resume files"""
        # TODO: Implement resume upload logic
        # This would typically involve:
        # - Processing uploaded files
        # - Storing file metadata in database
        # - Processing embeddings in background
        # - Saving files to S3 or local storage
        pass

    async def delete_resume(self, resume_id: UUID) -> bool:
        """Delete resume by ID"""
        resume = await self.get_resume_by_id(resume_id)
        if not resume:
            return False

        await self.session.delete(resume)
        await self.session.commit()
        return True
