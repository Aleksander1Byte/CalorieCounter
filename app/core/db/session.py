from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel
from app.core.db.engine import engine, async_session
from sqlalchemy.ext.asyncio import AsyncSession


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
