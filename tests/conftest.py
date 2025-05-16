import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from shared.db.base import Base
from app.main import app as fastapi_app
from shared.db.connection import get_session

# Create test database engine
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pw@localhost:5439/test_db"
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Disable connection pooling for tests
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any pending changes
        await session.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def app(db_session):
    """Create a fresh FastAPI app for each test."""
    # Override the get_session dependency
    async def _get_test_session():
        yield db_session

    fastapi_app.dependency_overrides[get_session] = _get_test_session
    yield fastapi_app
    fastapi_app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def async_client(app):
    """Create an async client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
