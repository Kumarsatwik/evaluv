from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import  create_async_engine
from typing import AsyncGenerator
from .config import settings


# Create async engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30
)


async def create_db_and_tables():
    """Create database tables"""
    async with async_engine.begin() as conn:
        # Drop tables in reverse dependency order to avoid FK issues
        await conn.run_sync(SQLModel.metadata.drop_all)
        # Create tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator:
    """Get async session for dependency injection"""
    from sqlmodel.ext.asyncio.session import AsyncSession
    
    async with AsyncSession(async_engine) as session:
        yield session
