from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from shared.db.connection import get_session
from shared.utils.logging import log_exceptions
import logging
from .models import MemberDB
from .schemas import MemberCreate, MemberOut

router = APIRouter()

@router.post("/members", response_model=MemberOut)
@log_exceptions
async def create_member(payload: MemberCreate, session: AsyncSession = Depends(get_session)):
    try:
        # Create new member
        new_member = MemberDB(**payload.model_dump())
        session.add(new_member)
        await session.commit()
        await session.refresh(new_member)
        return new_member
    except IntegrityError as e:
        await session.rollback()
        error_msg = str(e.orig).lower() if e.orig else str(e).lower()
        logging.error(f"IntegrityError: {error_msg}")  # Log the exact error message
        if "duplicate key value violates unique constraint" in error_msg:
            if "login" in error_msg:
                raise HTTPException(status_code=400, detail="Login already exists")
            if "email" in error_msg:
                raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail="Database error")
    except SQLAlchemyError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Database error")

@router.get("/members", response_model=list[MemberOut])
@log_exceptions
async def get_members(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(MemberDB).where(MemberDB.deleted == False).order_by(desc(MemberDB.followers))
    )
    return result.scalars().all()

@router.delete("/members")
@log_exceptions
async def soft_delete_members(session: AsyncSession = Depends(get_session)):
    await session.execute(update(MemberDB).values(deleted=True).where(MemberDB.deleted == False))
    await session.commit()
    return {"message": "Members soft deleted"}

@router.delete("/members/{member_id}")
@log_exceptions
async def soft_delete_member(member_id: int, session: AsyncSession = Depends(get_session)):
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
