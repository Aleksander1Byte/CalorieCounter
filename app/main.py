from fastapi import FastAPI

from app.core.db.session import init_db
from .api.v1.health import router as health_router

app = FastAPI()
app.include_router(health_router)


@app.on_event("startup")
async def on_startup():
    await init_db()
