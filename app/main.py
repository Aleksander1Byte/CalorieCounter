from fastapi import FastAPI

from app.core.db.session import init_db
from app.api.v1.api import v1_router

app = FastAPI()
app.include_router(v1_router)


@app.on_event("startup")
async def on_startup():
    await init_db()
