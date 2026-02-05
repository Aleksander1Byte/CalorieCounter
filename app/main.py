from fastapi import FastAPI

from app.core.db.session import init_db, SessionDep
from .api.v1.health import router as health_router
from .core.models.pydantic import MealEntry
from .core.models.repositories import MealEntryRepository, UserRepository
from .core.models.services import MealService

app = FastAPI()
app.include_router(health_router)


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/meal/{tg_id}/{text}")
async def meal_entry(session: SessionDep, tg_id: int, text: str) -> MealEntry:
    meal_repo = MealEntryRepository(session)
    user_repo = UserRepository(session)
    meal_service = MealService(user_repo, meal_repo)
    return await meal_service.log_meal(tg_id, text)
