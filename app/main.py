from fastapi import FastAPI

from app.api.v1.api import v1_router
from app.core.db.session import init_db

app = FastAPI()
app.include_router(v1_router)


@app.on_event("startup")
async def on_startup():
    await init_db()
