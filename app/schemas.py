from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class MealEntryCreateData(BaseModel):
    tg_user_id: int
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
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
