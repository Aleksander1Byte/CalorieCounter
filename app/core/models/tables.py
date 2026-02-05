from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, TIMESTAMP, ForeignKey, String, Float
from sqlalchemy.dialects.postgresql import JSONB

metadata_obj = MetaData()

user = Table(
    "user",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("tg_user_id", Integer, unique=True, nullable=False),
    Column("created_at", TIMESTAMP),
)

meal_entry = Table(
    "meal_entry",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), unique=True, nullable=False),
    Column("text", String(300), nullable=False),
    Column("eaten_at", TIMESTAMP),
    Column("calories", Integer),
    Column("protein", Integer),
    Column("fat", Integer),
    Column("carbs", Integer),
    Column("llm_raw", JSONB),
    Column("confidence", Float, nullable=False),
)
