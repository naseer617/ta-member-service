from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from shared.db.connection import get_session
from .models import MemberDB
from .schemas import MemberCreate, MemberOut

router = APIRouter()

@router.post("/members", response_model=MemberOut)
async def create_member(payload: MemberCreate, session: AsyncSession = Depends(get_session)):
    new_member = MemberDB(**payload.dict())
    session.add(new_member)
    await session.commit()
    await session.refresh(new_member)
    return new_member

@router.get("/members", response_model=list[MemberOut])
async def get_members(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MemberDB).where(MemberDB.deleted == False).order_by(desc(MemberDB.followers))
    )
    return result.scalars().all()

@router.delete("/members")
async def soft_delete_members(session: AsyncSession = Depends(get_session)):
    await session.execute(update(MemberDB).values(deleted=True).where(MemberDB.deleted == False))
    await session.commit()
    return {"message": "Members soft deleted"}
