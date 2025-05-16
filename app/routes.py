from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from shared.db.connection import get_session
from .models import MemberDB
from .schemas import MemberCreate, MemberOut

router = APIRouter()

@router.post("/members", response_model=MemberOut)
async def create_member(payload: MemberCreate, session: AsyncSession = Depends(get_session)):
    try:
        new_member = MemberDB(**payload.model_dump())
        session.add(new_member)
        await session.commit()
        await session.refresh(new_member)
        return new_member
    except IntegrityError as e:
        await session.rollback()
        error_msg = str(e).lower()
        if "members_login_key" in error_msg:
            raise HTTPException(status_code=400, detail="Login already exists")
        if "members_email_key" in error_msg:
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail="Database error")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Database error")

@router.get("/members", response_model=list[MemberOut])
async def get_members(session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(
            select(MemberDB).where(MemberDB.deleted == False).order_by(desc(MemberDB.followers))
        )
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch members")

@router.delete("/members")
async def soft_delete_members(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(update(MemberDB).values(deleted=True).where(MemberDB.deleted == False))
        await session.commit()
        return {"message": "Members soft deleted"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete members")

@router.delete("/members/{member_id}")
async def soft_delete_member(member_id: int, session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(
            update(MemberDB)
            .values(deleted=True)
            .where(MemberDB.id == member_id, MemberDB.deleted == False)
            .returning(MemberDB.id)
        )
        deleted_id = result.scalar_one_or_none()
        if not deleted_id:
            raise HTTPException(status_code=404, detail="Member not found")
        await session.commit()
        return {"message": f"Member {member_id} soft deleted"}
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete member")
