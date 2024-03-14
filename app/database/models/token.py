from datetime import datetime
from typing import Union

from sqlalchemy import ForeignKey, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.schemas.token import TokenCreateInput, TokenWithDeviceCreateInput


class RefreshSession(Base):
    __tablename__ = 'refresh_session'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now())
    expires_at: Mapped[datetime]
    revoked: Mapped[bool] = mapped_column(default=False)
    jti: Mapped[str]
    device_id: Mapped[str] = mapped_column(ForeignKey('user_device.device_id', ondelete='CASCADE'))

    @classmethod
    async def add_token_to_db(cls, session: AsyncSession, data: TokenWithDeviceCreateInput) -> None:
        token_data = TokenCreateInput(**data.model_dump(), device_id=data.device.device_id)
        token = cls(**token_data.model_dump())
        session.add(token)
        await session.commit()

    @classmethod
    async def revoke_active_tokens_for_user(
        cls, session: AsyncSession, user_id: str, device_id: str
    ) -> None:
        query = update(cls).where(cls.user_id == user_id, cls.device_id == device_id).values(revoked=True)
        await session.execute(query)
        await session.commit()

    @classmethod
    async def get_token_by_jti(cls, session: AsyncSession, jti: str) -> Union['RefreshSession', None]:
        query = select(cls).where(cls.jti == jti)
        token_entity = await session.execute(query)
        return token_entity.scalar()
