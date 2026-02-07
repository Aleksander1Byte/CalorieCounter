from datetime import datetime

from app.exceptions import (
    EmptyMealTextException,
    NotAFoodException,
    StrangeRequestException,
)
from app.repositories import MealEntryRepository, UserRepository
from app.schemas import (
    MealEntry,
    MealEntryCreateData,
    TgUserEntry,
    TgUserRepositoryCreateData,
)

from .llm.GeminiClient import GeminiClient

llm_client = GeminiClient()


class MealService:
    def __init__(
        self,
        user_repository: UserRepository,
        meal_entry_repository: MealEntryRepository,
    ):
        self.user_repository = user_repository
        self.meal_entry_repository = meal_entry_repository

    async def get_last_meal(self, tg_user_id) -> MealEntry:
        return await self.meal_entry_repository.get_last_meal(tg_user_id)

    async def delete_last_meal(self, tg_user_id) -> MealEntry:
        res = await self.meal_entry_repository.delete_last_meal(tg_user_id)
        if res:
            await self.meal_entry_repository.session.commit()
        return res

    async def today_meals(self, tg_user_id) -> dict:
        res = await self.meal_entry_repository.get_today_meals(tg_user_id)
        return {
            "calories": res[0],
            "protein": res[1],
            "fat": res[2],
            "carbs": res[3],
        }

    async def log_meal(
        self,
        tg_user_id: int,
        text: str,
        image_content: bytes = None,
        content_type: str = None,
    ) -> MealEntry:
        text = text.strip()
        if not text and image_content is None:
            raise EmptyMealTextException

        await self._get_user(tg_user_id)
        try:
            data = await llm_client.process(text, image_content, content_type)
        except StrangeRequestException:
            raise

        if data.get("calories_kcal") == -1:
            raise NotAFoodException

        if data.get("confidence") < 75:
            raise StrangeRequestException
        if data.get("image_desc") != -1:
            text = data.get("image_desc")

        data = MealEntryCreateData(
            tg_user_id=tg_user_id,
            text=text,
            created_at=datetime.now(),
            calories=data.get("calories_kcal"),
            protein=data.get("protein_g"),
            fat=data.get("fat_g"),
            carbs=data.get("carbs_g"),
            llm_raw=data,
            confidence=data.get("confidence"),
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
