from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.authentication import AuthenticationMiddleware

from app.api import auth_router, user_router
from app.auth.middleware import AuthBackend
from app.database.settings import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.create_tables()
    yield
    # await database.drop_tables()


app = FastAPI(lifespan=lifespan)
app.add_middleware(AuthenticationMiddleware, backend=AuthBackend())
app.include_router(auth_router)
app.include_router(user_router)
