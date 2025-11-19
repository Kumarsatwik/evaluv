from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from ..database import async_engine
from ..models.job import Job
from ..utils.embedding_utils import embedding_utils
from ..utils.qdrant_client import upsert_job_vector, delete_job_vector

async def process_job_embedding_task(job_id: UUID):
    """
    Background task to generate embedding and update status.
    """
    async with AsyncSession(async_engine) as session:
        # 1. Fetch the Job (Refresh from DB)
        statement = select(Job).where(Job.id == job_id)
        result = await session.exec(statement)
        job = result.first()
        
        if not job:
            return

        try:
            # 2. Generate Embedding (The heavy operation)
            # Using model_dump to turn SQLModel into dict
            vector = await embedding_utils.generate_job_embedding(job.model_dump())

            # 3. Upsert to Qdrant
            # We use the Postgres ID as the Qdrant Point ID
            qdrant_id = str(job.id) 
            
            payload = {
                "title": job.title,
                "company": getattr(job, "company", ""),
                "location": job.location,
                "skills": job.skills,
                "created_by": str(job.created_by),
                "postgres_id": qdrant_id
            }

            await upsert_job_vector(job_id=qdrant_id, vector=vector, payload=payload)

            # 4. Update Postgres Status: Success
            job.embedding_status = "completed"
            job.qdrant_point_id = qdrant_id
            job.error_message = None

        except Exception as e:
            # 5. Handle Failure
            print(f"Embedding failed for Job {job_id}: {e}")
            job.embedding_status = "failed"
            job.error_message = str(e)

        finally:
            # Save status change
            session.add(job)
            await session.commit()


async def delete_job_embedding_task(qdrant_point_id: str):
    """
    Background task to delete embedding from Qdrant.
    """
    try:
        if qdrant_point_id:
            await delete_job_vector(qdrant_point_id)
    except Exception as e:
        print(f"Embedding deletion failed for Qdrant Point ID {qdrant_point_id}: {e}")
