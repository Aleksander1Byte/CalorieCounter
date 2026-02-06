from typing import Annotated

from fastapi import Depends, Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.db.session import SessionDep
from app.repositories import MealEntryRepository, UserRepository
from app.services import MealService
from app.core.config import SECRET_KEY


def auth_header(key: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    if key.credentials != SECRET_KEY:
        raise HTTPException(status_code=401)


def get_meal_service(session: SessionDep) -> MealService:
    user_repo = UserRepository(session)
    meal_repo = MealEntryRepository(session)
    return MealService(user_repo, meal_repo)


MealServiceDep = Annotated[MealService, Depends(get_meal_service)]
