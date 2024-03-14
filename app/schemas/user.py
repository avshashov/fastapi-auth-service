from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator

from app.constants import UserRole
from app.errors import PasswordMismatchException


class UserBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserCreateInput(UserBase):
    password: SecretStr = Field(min_length=8, max_length=30)
    repeat_password: SecretStr = Field(min_length=8, max_length=30)

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserCreateInput':
        if self.password != self.repeat_password:
            raise PasswordMismatchException
        return self


class UserWithHash(UserBase):
    hashed_password: str


class UserOutput(UserBase):
    user_id: str

    model_config = ConfigDict(from_attributes=True)


class UserWithMetaOutput(UserOutput):
    created_at: datetime
    disabled: bool
    role: UserRole
