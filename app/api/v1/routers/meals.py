from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    UploadFile,
    File,
    Form,
)
from httpx import HTTPStatusError

from app.exceptions import (
    EmptyMealTextException,
    NotAFoodException,
    StrangeRequestException,
)
from app.schemas import MealEntry

from ..deps import MealServiceDep, auth_header

router = APIRouter(
    prefix="/meal",
    tags=["meals"],
    dependencies=[Depends(auth_header)],
)


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


@router.get(
    "/today",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "calories": 100,
                        "protein": 25,
                        "fat": 10,
                        "carbs": 30,
                    }
                }
            },
        }
    },
)
async def today(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
) -> dict:
    res = await meal_service.today_meals(x_tg_user_id)
    if res is None:
        raise HTTPException(status_code=404, detail="No meals")
    return await meal_service.today_meals(x_tg_user_id)


@router.post("/")
async def meal_entry(
    meal_service: MealServiceDep,
    x_tg_user_id: Annotated[int, Header()],
    text: Annotated[str, Form(...)],
    file: Annotated[UploadFile | None, File] = File(None),
) -> MealEntry:
    try:
        if file:
            image_content = await file.read()
            return await meal_service.log_meal(
                x_tg_user_id, text, image_content, file.content_type
            )
        return await meal_service.log_meal(x_tg_user_id, text)
    except EmptyMealTextException:
        raise HTTPException(status_code=400, detail="Empty request")
    except NotAFoodException:
        raise HTTPException(status_code=400, detail="Not a food")
    except StrangeRequestException:
        raise HTTPException(
            status_code=400, detail="Try to describe it differently"
        )
    except HTTPStatusError:
        raise HTTPException(status_code=429, detail="Try again later")
