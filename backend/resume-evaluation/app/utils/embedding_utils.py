"""
Embedding utilities using OpenRouter via OpenAI client
"""
from typing import List

from openai import AsyncOpenAI
from ..config import settings


class EmbeddingUtils:
    """Embedding utility class for generating vector embeddings using OpenRouter"""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = getattr(settings, 'EMBEDDING_MODEL', 'qwen/qwen3-embedding-8b')
        self.client = None
        self.dimensions = 4096  # For qwen/qwen3-embedding-8b

    def is_available(self) -> bool:
        """Check if OpenRouter API key is configured"""
        return bool(self.api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenRouter"""
        if not self.api_key:
            raise Exception("OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.")

        if not self.client:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"
            )

        try:
            response = await self.client.embeddings.create(
                input=[text],
                model=self.model
            )

            if not response.data or len(response.data) == 0:
                raise Exception("No embedding data received from OpenRouter")

            embedding = response.data[0].embedding

            # Validate and return
            if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                return [float(x) for x in embedding]
            else:
                raise Exception("Invalid embedding format from OpenRouter")

        except Exception as e:
            raise Exception(f"OpenRouter embedding failed: {str(e)}")

    async def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.dimensions

    async def generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using configured provider"""
        if not text or len(text.strip()) == 0:
            # Return zero vector for empty text
            return [0.0] * self.dimensions

        return await self.generate_embedding(text)

    async def generate_job_embedding(self, job_data: dict) -> List[float]:
        """
        Generate embedding for job data combining title, description, and skills
        """
        # Combine relevant job fields for embedding
        text_parts = []
        if job_data.get('title'):
            text_parts.append(f"Job Title: {job_data['title']}")
        if job_data.get('description'):
            text_parts.append(f"Description: {job_data['description']}")
        if job_data.get('skills'):
            text_parts.append(f"Required Skills: {job_data['skills']}")
        if job_data.get('experience'):
            text_parts.append(f"Experience Required: {job_data['experience']}")
        if job_data.get('location'):
            text_parts.append(f"Location: {job_data['location']}")

        combined_text = ". ".join(text_parts)
        return await self.generate_text_embedding(combined_text)

    async def generate_resume_embedding(self, resume_data: dict) -> List[float]:
        """
        Generate embedding for resume data combining skills, experience, and summary
        """
        # Combine relevant resume fields for embedding
        text_parts = []
        if resume_data.get('name'):
            text_parts.append(f"Name: {resume_data['name']}")
        if resume_data.get('skills'):
            text_parts.append(f"Skills: {resume_data['skills']}")
        if resume_data.get('experience'):
            text_parts.append(f"Experience: {resume_data['experience']}")
        if resume_data.get('summary'):
            text_parts.append(f"Professional Summary: {resume_data['summary']}")
        if resume_data.get('education'):
            text_parts.append(f"Education: {resume_data['education']}")
        if resume_data.get('current_position'):
            text_parts.append(f"Current Position: {resume_data['current_position']}")

        combined_text = ". ".join(text_parts)
        return await self.generate_text_embedding(combined_text)


# Global embedding utility instance
embedding_utils = EmbeddingUtils()


def get_embedding_utils() -> EmbeddingUtils:
    """Dependency to get embedding utility instance"""
    return embedding_utils
