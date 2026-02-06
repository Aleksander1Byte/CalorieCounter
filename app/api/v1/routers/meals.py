from typing import Annotated

from fastapi import APIRouter, HTTPException, Body, Depends, Header

from ..deps import MealServiceDep, auth_header
from app.core.exceptions import EmptyMealTextError
from app.schemas import MealEntry

router = APIRouter(prefix="/meal", tags=["meals"], dependencies=[Depends(auth_header)])


@router.get("/last")
async def get_last_meal(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
) -> MealEntry:
    entry = await meal_service.get_last_meal(x_tg_user_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="No meals")
    return entry


@router.delete("/last")
async def delete_last_meal(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
) -> MealEntry:
    entry = await meal_service.delete_last_meal(x_tg_user_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="No meals")
    return entry


@router.get("/today")
async def today(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
) -> list[MealEntry]:
    return await meal_service.today_meals(x_tg_user_id)


@router.post("/")
async def meal_entry(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
    text: Annotated[str, Body(embed=True)],
) -> MealEntry:
    try:
        return await meal_service.log_meal(x_tg_user_id, text)
    except EmptyMealTextError:
        raise HTTPException(status_code=400, detail="The text field is empty")
