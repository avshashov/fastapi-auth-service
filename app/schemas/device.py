from pydantic import BaseModel


class UserDeviceInput(BaseModel):
    device_id: str
    ip_address: str
    user_agent: str
