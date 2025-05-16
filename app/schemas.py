from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class MemberBase(BaseModel):
    first_name: str
    last_name: str
    login: str
    email: EmailStr
    avatar_url: Optional[str] = None
    title: Optional[str] = None
    followers: int = 0
    following: int = 0

class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None = None
    followers: int = 0
    following: int = 0
    title: str | None = None
    email: EmailStr

class Member(MemberCreate):
    id: int
    deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None
    followers: int
    following: int
    title: str | None
    email: str
    created_at: datetime
    updated_at: datetime
