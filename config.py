from pydantic import BaseModel, field_validator, model_validator
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings
from pathlib import Path


class Database(BaseModel):
    dbms: str
    driver: str | None
    host: str
    port: int | None
    user: str
    password: str | None
    database: str
    echo_db: bool


class AuthenticationSettings(BaseModel):
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int
    private_key: Path
    public_key: Path | None

    @field_validator('public_key', 'private_key')
    @classmethod
    def read_key_from_file(cls, key_path: Path | None) -> str:
        if key_path:
            return key_path.read_text()

    @model_validator(mode='after')
    def change_key_by_algorithm(self) -> 'AuthenticationSettings':
        if self.algorithm in ('HS256', 'HS384', 'HS512'):
            self.public_key = self.private_key
        return self


class Settings(YamlBaseSettings):
    database: Database
    authentication: AuthenticationSettings

    model_config = SettingsConfigDict(yaml_file='config.yaml')


settings = Settings()

PUBLIC_KEY = settings.authentication.public_key
PRIVATE_KEY = settings.authentication.private_key
ALGORITHM = settings.authentication.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.authentication.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.authentication.refresh_token_expire_minutes
