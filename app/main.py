from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc, Integer, String, Boolean
from sqlalchemy.orm import mapped_column
from pydantic import BaseModel, EmailStr
import asyncio
from sqlalchemy.exc import OperationalError

# Shared DB module (monorepo)
from shared.db.connection import get_session, engine
from shared.db.base import Base

# FastAPI app
app = FastAPI(title="Member Service")

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

# Pydantic Request Model
class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None = None
    followers: int = 0
    following: int = 0
    title: str | None = None
    email: EmailStr

# Pydantic Response Model
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
        from_attributes = True  # for Pydantic v2

# DB startup with retries
@app.on_event("startup")
async def startup():
    retries = 10
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database connected and initialized.")
            break
        except OperationalError as e:
            print(f"⏳ DB not ready (attempt {attempt + 1}/{retries}), retrying...")
            await asyncio.sleep(2)
    else:
        raise RuntimeError("Database failed to connect after multiple retries.")

# API endpoints
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
