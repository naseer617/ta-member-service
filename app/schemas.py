from pydantic import BaseModel, EmailStr

class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    login: str
    avatar_url: str | None = None
    followers: int = 0
    following: int = 0
    title: str | None = None
    email: EmailStr

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
        from_attributes = True
