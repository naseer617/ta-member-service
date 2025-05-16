from sqlalchemy import Integer, String, Boolean, DateTime, func, Index
from sqlalchemy.orm import mapped_column
from shared.db.base import Base

class MemberDB(Base):
    __tablename__ = "members"

    id = mapped_column(Integer, primary_key=True, index=True)
    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)
    login = mapped_column(String, nullable=False)
    avatar_url = mapped_column(String, nullable=True)
    followers = mapped_column(Integer, default=0)
    following = mapped_column(Integer, default=0)
    title = mapped_column(String, nullable=True)
    email = mapped_column(String, nullable=False)
    deleted = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Partial unique indexes that only apply to non-deleted members
    __table_args__ = (
        Index('ix_members_login_unique', 'login', unique=True, postgresql_where=deleted == False),
        Index('ix_members_email_unique', 'email', unique=True, postgresql_where=deleted == False),
    )
