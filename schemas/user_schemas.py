import re

from pydantic import BaseModel, EmailStr, field_validator
from pydantic.fields import FieldInfo, Field


class UserCreate(BaseModel):
    email: EmailStr
    password : str = Field(min_length=8, max_length=72)



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    provider: str
    provider_id: str | None = None



