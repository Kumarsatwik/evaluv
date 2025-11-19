"""
Qdrant vector database client utilities
"""
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import Response
import numpy as np
from ..config import settings


class QdrantVectorClient:
    """Qdrant client wrapper for vector operations in resume evaluation"""

    def __init__(self):
        self.client: Optional[QdrantClient] = None

    async def connect(self):
        """Connect to Qdrant"""
        if not self.client:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                prefer_grpc=False  # Use REST API for compatibility
            )
        return self.client

    async def disconnect(self):
        """Disconnect from Qdrant"""
        if self.client:
            # Qdrant client doesn't need explicit disconnection
            self.client = None

    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        if not self.client:
            return False
        try:
            self.client.health_check()
            return True
        except Exception:
            return False

    # Job Collection Operations
    async def create_job_collection(self) -> bool:
        """Create collection for job embeddings"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_jobs"

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection_name in collection_names:
                # Check vector size
                info = self.client.get_collection(collection_name)
                current_size = info.config.params.vectors.size
                expected_size = settings.QDRANT_VECTOR_SIZE
                if current_size != expected_size:
                    print(f"Vector size mismatch for {collection_name}: expected {expected_size}, got {current_size}. Deleting and recreating...")
                    self.client.delete_collection(collection_name)
                else:
                    return True  # Already exists with correct size

            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=models.Distance.COSINE if settings.QDRANT_DISTANCE_METRIC == "Cosine"
                           else models.Distance.EUCLID,
                ),
                hnsw_config={
                    "m": 16,
                    "ef_construct": 100,
                    "full_scan_threshold": 10000,
                    "max_indexing_threads": 0,
                } if settings.QDRANT_ENABLE_HNSW else None,
            )
            print(f"Created job collection: {collection_name}")
            return True
        except Exception as e:
            print(f"Error creating job collection: {e}")
            return False

    async def index_job(self, job_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a job with its vector embedding"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_jobs"

        try:
            # Ensure collection exists
            await self.create_job_collection()

            # Convert to numpy array
            vector_array = np.array(vector, dtype=np.float32)

            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=hash(job_id) % 2**63,  # Use hash as numeric ID
                        vector=vector_array.tolist(),
                        payload={
                            "job_id": job_id,
                            **metadata
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error indexing job {job_id}: {e}")
            return False

    async def search_similar_jobs(self, query_vector: List[float], limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for similar jobs using vector similarity"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_jobs"

        try:
            # Convert to numpy array
            query_array = np.array(query_vector, dtype=np.float32)

            # Build filter if provided
            query_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                query_filter = models.Filter(must=must_conditions)

            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_array.tolist(),
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "job_id": hit.payload["job_id"],
                    "score": hit.score,
                    "metadata": {k: v for k, v in hit.payload.items() if k != "job_id"}
                })

            return results
        except Exception as e:
            print(f"Error searching similar jobs: {e}")
            return []

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job from the vector index"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_jobs"

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[hash(job_id) % 2**63]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return False

    # Resume/Candidate Collection Operations
    async def create_resume_collection(self) -> bool:
        """Create collection for resume embeddings"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_resumes"

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if collection_name in collection_names:
                # Check vector size
                info = self.client.get_collection(collection_name)
                current_size = info.config.params.vectors.size
                expected_size = settings.QDRANT_VECTOR_SIZE
                if current_size != expected_size:
                    print(f"Vector size mismatch for {collection_name}: expected {expected_size}, got {current_size}. Deleting and recreating...")
                    self.client.delete_collection(collection_name)
                else:
                    return True  # Already exists with correct size

            # Create new collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=settings.QDRANT_VECTOR_SIZE,
                    distance=models.Distance.COSINE if settings.QDRANT_DISTANCE_METRIC == "Cosine"
                           else models.Distance.EUCLID,
                ),
                hnsw_config={
                    "m": 16,
                    "ef_construct": 100,
                    "full_scan_threshold": 10000,
                    "max_indexing_threads": 0,
                } if settings.QDRANT_ENABLE_HNSW else None,
            )
            print(f"Created resume collection: {collection_name}")
            return True
        except Exception as e:
            print(f"Error creating resume collection: {e}")
            return False

    async def index_resume(self, resume_id: str, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Index a resume with its vector embedding"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_resumes"

        try:
            # Ensure collection exists
            await self.create_resume_collection()

            # Convert to numpy array
            vector_array = np.array(vector, dtype=np.float32)

            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=hash(resume_id) % 2**63,  # Use hash as numeric ID
                        vector=vector_array.tolist(),
                        payload={
                            "resume_id": resume_id,
                            **metadata
                        }
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Error indexing resume {resume_id}: {e}")
            return False

    async def search_matching_resumes(self, job_vector: List[float], limit: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search for resumes that match a job using vector similarity"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_resumes"

        try:
            # Convert to numpy array
            query_array = np.array(job_vector, dtype=np.float32)

            # Build filter if provided
            query_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                query_filter = models.Filter(must=must_conditions)

            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_array.tolist(),
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "resume_id": hit.payload["resume_id"],
                    "score": hit.score,
                    "metadata": {k: v for k, v in hit.payload.items() if k != "resume_id"}
                })

            return results
        except Exception as e:
            print(f"Error searching matching resumes: {e}")
            return []

    async def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume from the vector index"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_resumes"

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[hash(resume_id) % 2**63]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting resume {resume_id}: {e}")
            return False

    # Utility Methods
    async def get_collection_info(self, collection_type: str) -> Optional[Dict]:
        """Get information about a collection"""
        if not self.client:
            await self.connect()

        collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_{collection_type}"

        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": info.config.name,
                "vectors_count": info.vectors_count,
                "status": info.status,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return None


# Global Qdrant client instance
qdrant_client = QdrantVectorClient()


async def get_qdrant_client():
    """Dependency to get Qdrant client"""
    await qdrant_client.connect()
    return qdrant_client


async def upsert_job_vector(job_id: str, vector: List[float], payload: Dict[str, Any]) -> bool:
    """Upsert job vector to Qdrant"""
    await qdrant_client.connect()
    return await qdrant_client.index_job(job_id, vector, payload)


async def delete_job_vector(qdrant_point_id: str) -> bool:
    """Delete job vector from Qdrant"""
    await qdrant_client.connect()
    return await qdrant_client.delete_job(qdrant_point_id)
