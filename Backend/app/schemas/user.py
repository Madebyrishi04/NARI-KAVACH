
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8)
    phone_number: str | None = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: str | None = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str
    phone_number: str | None = None


class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: str | None = None

    class Config:
        from_attributes = True

