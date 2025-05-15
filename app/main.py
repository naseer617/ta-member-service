from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update, desc
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, Boolean
from pydantic import BaseModel, EmailStr
import asyncio
from sqlalchemy.exc import OperationalError
import os

# Environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "member_db")
DB_USER = os.getenv("DB_USER", "member_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_pw")
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI app
app = FastAPI(title="Member Service")

# Database Dependency
async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# DB Model
class MemberDB(Base):
    __tablename__ = "members"

    id = mapped_column(Integer, primary_key=True, index=True)
    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)
    login = mapped_column(String, unique=True, nullable=False)
    avatar_url = mapped_column(String, nullable=True)
    followers = mapped_column(Integer, default=0)
    following = mapped_column(Integer, default=0)
    title = mapped_column(String, nullable=True)
    email = mapped_column(String, unique=True, nullable=False)
    deleted = mapped_column(Boolean, default=False)

# Request Model
class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None = None
    followers: int = 0
    following: int = 0
    title: str | None = None
    email: EmailStr

# Response Model
class MemberOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None
    followers: int
    following: int
    title: str | None
    email: EmailStr

    class Config:
        orm_mode = True

# Startup DB table creation
# Routes
@app.on_event("startup")
async def startup():
    retries = 10
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database connected and initialized.")
            break
        except OperationalError as e:
            print(f"⏳ DB not ready (attempt {attempt + 1}/{retries}), retrying...")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("❌ Database failed to connect after multiple retries.")

# Routes
@app.post("/members", response_model=MemberOut)
async def create_member(payload: MemberCreate, session: AsyncSession = Depends(get_session)):
    new_member = MemberDB(**payload.dict())
    session.add(new_member)
    await session.commit()
    await session.refresh(new_member)
    return new_member

@app.get("/members", response_model=list[MemberOut])
async def get_members(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MemberDB).where(MemberDB.deleted == False).order_by(desc(MemberDB.followers))
    )
    return result.scalars().all()

@app.delete("/members")
async def soft_delete_members(session: AsyncSession = Depends(get_session)):
    await session.execute(update(MemberDB).values(deleted=True).where(MemberDB.deleted == False))
    await session.commit()
    return {"message": "Members soft deleted"}
