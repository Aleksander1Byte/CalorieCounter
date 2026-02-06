from sqlalchemy.ext.asyncio import AsyncSession

from .pydantic import (
    MealEntryCreateData,
    MealEntry,
    TgUserRepositoryCreateData,
    TgUserEntry,
)
from .tables import meal_entry, tg_user
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, data: TgUserRepositoryCreateData) -> TgUserEntry:
        stmt = insert(tg_user).values(
            tg_user_id=data.tg_user_id, created_at=data.created_at
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[tg_user.c.tg_user_id],
            set_=dict(tg_user_id=stmt.excluded.tg_user_id),
        ).returning(tg_user.c.id, tg_user.c.tg_user_id, tg_user.c.created_at)
        res = await self.session.execute(stmt)
        row = res.one()
        return TgUserEntry(
            id=row.id, tg_user_id=row.tg_user_id, created_at=row.created_at
        )


class MealEntryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_entry(self, data: MealEntryCreateData) -> MealEntry:
        payload = data.model_dump()
        stmt = (
            insert(meal_entry)
            .values(**payload)
            .returning(
                meal_entry.c.id,
                meal_entry.c.tg_user_id,
                meal_entry.c.text,
                meal_entry.c.created_at,
                meal_entry.c.calories,
                meal_entry.c.protein,
                meal_entry.c.fat,
                meal_entry.c.carbs,
                meal_entry.c.llm_raw,
                meal_entry.c.confidence,
            )
        )
        res = await self.session.execute(stmt)
        row = res.one()
        return MealEntry(
            id=row.id,
            tg_user_id=row.tg_user_id,
            text=row.text,
            created_at=row.created_at,
            calories=row.calories,
            protein=row.protein,
            fat=row.fat,
            carbs=row.carbs,
            llm_raw=row.llm_raw,
            confidence=row.confidence,
        )

    async def list_for_day(self, tg_user_id: int, day: datetime):
        pass

    async def delete_last(self, tg_user_id):
        pass
