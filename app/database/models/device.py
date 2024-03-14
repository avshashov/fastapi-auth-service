from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.schemas import UserDeviceInput


class UserDevice(Base):
    __tablename__ = 'user_device'

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(unique=True)
    ip_address: Mapped[str]
    user_agent: Mapped[str]

    @classmethod
    async def add_user_device_to_db(cls, session: AsyncSession, user_device: UserDeviceInput) -> None:
        if not await cls.check_exists_user_device(session, device_id=user_device.device_id):
            device = UserDevice(**user_device.model_dump())
            session.add(device)
            await session.commit()

    @classmethod
    async def check_exists_user_device(cls, session: AsyncSession, device_id: str) -> bool:
        query = select(UserDevice).where(UserDevice.device_id == device_id)
        device = await session.execute(query)
        return bool(device.scalars().first())
