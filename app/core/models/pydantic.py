from datetime import datetime
from typing import Any
from pydantic import BaseModel


class MealEntryCreateData(BaseModel):
    user_id: int
    text: str
    eaten_at: datetime
    calories: int
    protein: int
    fat: int
    carbs: int
    llm_raw: dict[str, Any]
    confidence: float


class MealEntry(MealEntryCreateData):
    id: int


class TgUserRepositoryCreateData(BaseModel):
    tg_user_id: int
    created_at: datetime


class TgUserEntry(TgUserRepositoryCreateData):
    id: int
