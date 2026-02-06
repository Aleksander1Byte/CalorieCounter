from sqlalchemy import (TIMESTAMP, Column, ForeignKey, Integer, MetaData,
                        Numeric, String, Table)
from sqlalchemy.dialects.postgresql import JSONB

metadata_obj = MetaData()

tg_user = Table(
    "tg_user",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("tg_user_id", Integer, unique=True, nullable=False),
    Column("created_at", TIMESTAMP),
)

meal_entry = Table(
    "meal_entry",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("tg_user_id", Integer, ForeignKey("tg_user.tg_user_id"), nullable=False),
    Column("text", String(300), nullable=False),
    Column("created_at", TIMESTAMP),
    Column("calories", Integer),
    Column("protein", Numeric(6, 1)),
    Column("fat", Numeric(6, 1)),
    Column("carbs", Numeric(6, 1)),
    Column("llm_raw", JSONB),
    Column("confidence", Integer, nullable=False),
)
