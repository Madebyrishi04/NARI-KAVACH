
from pydantic import BaseModel, Field, EmailStr


class EmergencyContactCreate(BaseModel):
    contact_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=10, max_length=20)
    email: EmailStr | None = None
    relationship: str | None = None


class EmergencyContactResponse(BaseModel):
    id: int
    contact_name: str
    phone_number: str
    email: str | None = None
    relationship: str | None = None

    class Config:
        from_attributes = True
