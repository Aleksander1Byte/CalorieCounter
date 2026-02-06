from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MealEntryCreateData(BaseModel):
    tg_user_id: int
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    calories: int
    protein: float = Field(ge=0, decimal_places=1)
    fat: float = Field(ge=0, decimal_places=1)
    carbs: float = Field(ge=0, decimal_places=1)
    llm_raw: dict[str, Any]
    confidence: int


class MealEntry(MealEntryCreateData):
    id: int


class TgUserRepositoryCreateData(BaseModel):
    tg_user_id: int
    created_at: datetime


class TgUserEntry(TgUserRepositoryCreateData):
    id: int
