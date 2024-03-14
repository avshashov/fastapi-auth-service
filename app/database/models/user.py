import uuid
from datetime import datetime
from typing import Union

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.constants import UserRole
from app.database.models.base import Base
from app.errors import UserAlreadyExistsException
from app.schemas import UserWithHash


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(unique=True)
    full_name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    disabled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    role: Mapped[str] = mapped_column(default=UserRole.USER)

    @classmethod
    async def create_user(cls, session: AsyncSession, user_data: UserWithHash) -> 'User':
        user_exists = await cls.check_user_exists(
            session, email=user_data.email
        )
        if user_exists:
            raise UserAlreadyExistsException
        user_id = str(uuid.uuid5(uuid.NAMESPACE_X500, user_data.email))
        stmt = insert(cls).values(user_id=user_id, **user_data.model_dump()).returning(cls)
        user = await session.execute(stmt)
        await session.commit()
        return user.scalar()

    @classmethod
    async def get_user_by_user_id(cls, session: AsyncSession, user_id: str) -> Union['User', None]:
        stmt = select(cls).where(cls.user_id == user_id)
        user = await session.execute(stmt)
        return user.scalar()

    @classmethod
    async def get_user_by_email(cls, session: AsyncSession, email: str) -> Union['User', None]:
        stmt = select(cls).where(cls.email == email)
        user = await session.execute(stmt)
        return user.scalar()

    @classmethod
    async def check_user_exists(cls, session: AsyncSession, email: str) -> bool:
        stmt = select(cls).where(cls.email == email)
        user = await session.execute(stmt)
        return bool(user.scalars().all())
