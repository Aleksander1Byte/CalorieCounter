from typing import Annotated

from fastapi import Depends

from app.core.db.session import SessionDep
from app.repositories import MealEntryRepository, UserRepository
from app.services import MealService


def get_meal_service(session: SessionDep) -> MealService:
    user_repo = UserRepository(session)
    meal_repo = MealEntryRepository(session)
    return MealService(user_repo, meal_repo)


MealServiceDep = Annotated[MealService, Depends(get_meal_service)]
