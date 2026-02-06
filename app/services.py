from datetime import datetime

from app.schemas import (
    TgUserEntry,
    MealEntry,
    TgUserRepositoryCreateData,
    MealEntryCreateData,
)
from app.repositories import MealEntryRepository, UserRepository
from app.core.exceptions import EmptyMealTextError


class MealService:
    def __init__(
        self,
        user_repository: UserRepository,
        meal_entry_repository: MealEntryRepository,
    ):
        self.user_repository = user_repository
        self.meal_entry_repository = meal_entry_repository

    async def today_meals(self, tg_user_id) -> list[MealEntry]:
        await self._get_user(tg_user_id)
        return await self.meal_entry_repository.get_today_meals(tg_user_id)

    async def log_meal(self, tg_user_id, text) -> MealEntry:
        # TODO: add LLM
        text = text.strip()
        if not text:
            raise EmptyMealTextError

        await self._get_user(tg_user_id)

        data = MealEntryCreateData(
            tg_user_id=tg_user_id,
            text=text,
            created_at=datetime.now(),
            calories=100,
            protein=12,
            fat=5,
            carbs=20,
            llm_raw={"test": "yes"},
            confidence=1.0,
        )
        res = await self.meal_entry_repository.add_entry(data)
        await self.meal_entry_repository.session.commit()
        return res

    async def _get_user(self, tg_user_id: int) -> TgUserEntry:
        data = TgUserRepositoryCreateData(
            tg_user_id=tg_user_id, created_at=datetime.now()
        )
        res = await self.user_repository.get_or_create(data)
        await self.user_repository.session.commit()
        return res
