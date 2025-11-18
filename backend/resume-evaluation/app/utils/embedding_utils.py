"""
Embedding utilities using Ollama (local) and OpenAI (production)
"""
import asyncio
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import json
import hashlib
import numpy as np

from openai import AsyncOpenAI
from ..config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        pass

    @abstractmethod
    async def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider for local inference"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_EMBEDDING_MODEL
        self._available = False
        self._dimensions = 1024  # Most Ollama embedding models use 1024 dimensions

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        if not self.is_available():
            raise Exception("Ollama is not available. Make sure Ollama is running and accessible.")

        try:
            import aiohttp

            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": text,
                "stream": False,
                "options": {
                    "embedding_only": True
                }
            }

            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url.rstrip('/')}/api/embeddings",
                    json=payload
                ) as response:

                    if response.status != 200:
                        raise Exception(f"Ollama API returned status {response.status}: {await response.text()}")

                    result = await response.json()

                    if "embedding" not in result:
                        raise Exception("No embedding found in Ollama response")

                    # Ensure result is a list of floats
                    embedding = result["embedding"]
                    if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                        return [float(x) for x in embedding]
                    else:
                        raise Exception("Invalid embedding format from Ollama")

        except ImportError:
            raise Exception("aiohttp is required for Ollama. Install with: pip install aiohttp")
        except Exception as e:
            # Fallback to hash-based embedding if Ollama fails
            print(f"Ollama embedding failed: {e}, falling back to hash-based")
            return self._fallback_embedding(text)

    async def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self._dimensions

    def is_available(self) -> bool:
        """Check if Ollama is available by testing the connection"""
        try:
            import aiohttp
            import asyncio

            async def test_connection():
                try:
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(f"{self.base_url.rstrip('/')}/api/tags") as response:
                            return response.status == 200
                except:
                    return False

            # Run in new event loop to avoid nesting issues
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(test_connection())
                self._available = result
                return result
            finally:
                loop.close()

        except ImportError:
            return False
        except Exception:
            return False

    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback hash-based embedding when Ollama fails"""
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()

        # Convert hash to fixed-size embedding
        embedding = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                value = int.from_bytes(chunk, byteorder='little', signed=False)
                # Normalize to [-1, 1]
                normalized = (value % 2000) / 1000.0 - 1.0
                embedding.append(normalized)

        # Pad to target dimensions
        while len(embedding) < self._dimensions:
            embedding.extend(embedding[:self._dimensions - len(embedding)])

        embedding = embedding[:self._dimensions]

        # L2 normalize
        vector_array = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(vector_array)
        if norm > 0:
            embedding = (vector_array / norm).tolist()

        return embedding


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider for production use"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.client: Optional[AsyncOpenAI] = None
        self._dimensions = 1536  # Depends on model

        # Set dimensions based on model
        if self.model == "text-embedding-ada-002":
            self._dimensions = 1536
        elif self.model == "text-embedding-3-small":
            self._dimensions = 1536
        elif self.model == "text-embedding-3-large":
            self._dimensions = 3072

    def is_available(self) -> bool:
        """Check if OpenAI API key is configured"""
        return bool(self.api_key and self.api_key.startswith("sk-"))

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        if not self.api_key:
            raise Exception("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")

        if not self.client:
            self.client = AsyncOpenAI(api_key=self.api_key)

        try:
            # Truncate text if too long
            truncated_text = text[:settings.EMBEDDING_MAX_TOKENS]

            response = await self.client.embeddings.create(
                input=[truncated_text],
                model=self.model
            )

            if not response.data or len(response.data) == 0:
                raise Exception("No embedding data received from OpenAI")

            embedding = response.data[0].embedding

            # Validate and return
            if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                return [float(x) for x in embedding]
            else:
                raise Exception("Invalid embedding format from OpenAI")

        except Exception as e:
            raise Exception(f"OpenAI embedding failed: {str(e)}")

    async def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self._dimensions


class EmbeddingUtils:
    """Main embedding utility class with provider selection"""

    def __init__(self):
        self.provider: Optional[EmbeddingProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the appropriate embedding provider based on environment"""
        environment = settings.ENVIRONMENT.lower()

        if environment == "production":
            # Use OpenAI in production
            if settings.OPENAI_API_KEY:
                self.provider = OpenAIEmbeddingProvider()
            else:
                print("Warning: Production environment detected but OPENAI_API_KEY not set. Falling back to Ollama.")
                self.provider = OllamaEmbeddingProvider()
        elif environment == "development":
            # Use Ollama in development
            self.provider = OllamaEmbeddingProvider()
        else:
            # Default to development (Ollama)
            print(f"Warning: Unknown environment '{environment}', defaulting to Ollama for development.")
            self.provider = OllamaEmbeddingProvider()

    async def ensure_provider_available(self):
        """Ensure the chosen provider is available"""
        if not self.provider:
            raise Exception("No embedding provider configured")

        if not self.provider.is_available():
            # If Ollama is not available, try to fall back to hash-based
            if isinstance(self.provider, OllamaEmbeddingProvider):
                print("Warning: Ollama not available, using fallback hash-based embeddings")
            else:
                raise Exception(f"Embedding provider {settings.EMBEDDING_PROVIDER} is not available")

    async def generate_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using configured provider"""
        await self.ensure_provider_available()

        if not text or len(text.strip()) == 0:
            # Return zero vector for empty text
            return [0.0] * (await self.get_dimensions())

        return await self.provider.generate_embedding(text)

    async def get_dimensions(self) -> int:
        """Get embedding dimensions for current provider"""
        if not self.provider:
            return 768  # Default fallback
        return await self.provider.get_dimensions()

    def is_provider_available(self) -> bool:
        """Check if the current provider is available"""
        return self.provider is not None and self.provider.is_available()

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

    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding is properly formatted"""
        if not isinstance(embedding, list):
            return False

        expected_dims = 768 if isinstance(self.provider, OllamaEmbeddingProvider) else self.provider._dimensions
        if len(embedding) != expected_dims:
            return False

        # Check that all values are floats and within reasonable range
        try:
            for value in embedding:
                if not isinstance(value, (int, float)):
                    return False
                if abs(value) > 2.0:  # Allow some tolerance beyond [-1, 1]
                    return False
        except (TypeError, ValueError):
            return False

        return True

    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current embedding provider"""
        provider_name = "ollama" if isinstance(self.provider, OllamaEmbeddingProvider) else "openai"
        return {
            "environment": settings.ENVIRONMENT,
            "provider": provider_name,
            "is_available": self.is_provider_available(),
            "dimensions": 768 if isinstance(self.provider, OllamaEmbeddingProvider) else getattr(self.provider, '_dimensions', 1536)
        }


# Global embedding utility instance
embedding_utils = EmbeddingUtils()


def get_embedding_utils() -> EmbeddingUtils:
    """Dependency to get embedding utility instance"""
    return embedding_utils
