from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import mapped_column
from shared.db.base import Base

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
