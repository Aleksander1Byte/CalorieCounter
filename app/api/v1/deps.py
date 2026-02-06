from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import SECRET_KEY
from app.core.db.session import SessionDep
from app.repositories import MealEntryRepository, UserRepository
from app.services import MealService


def auth_header(key: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    if key.credentials != SECRET_KEY:
        raise HTTPException(status_code=401)


def get_meal_service(session: SessionDep) -> MealService:
    user_repo = UserRepository(session)
    meal_repo = MealEntryRepository(session)
    return MealService(user_repo, meal_repo)


MealServiceDep = Annotated[MealService, Depends(get_meal_service)]
