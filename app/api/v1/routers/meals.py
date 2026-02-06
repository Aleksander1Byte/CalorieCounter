from fastapi import APIRouter, HTTPException

from ..deps import MealServiceDep
from app.core.exceptions import EmptyMealTextError
from app.schemas import MealEntry

router = APIRouter(prefix="/meal", tags=["meals"])


@router.get("/{tg_id}/today")
async def today(meal_service: MealServiceDep, tg_id: int) -> list[MealEntry]:
    return await meal_service.today_meals(tg_id)


@router.get("/{tg_id}/{text}")
async def meal_entry(meal_service: MealServiceDep, tg_id: int, text: str) -> MealEntry:
    try:
        return await meal_service.log_meal(tg_id, text)
    except EmptyMealTextError:
        raise HTTPException(status_code=400, detail="The text field is empty")
