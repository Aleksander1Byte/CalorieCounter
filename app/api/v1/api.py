from fastapi import APIRouter
from app.api.v1.routers.health import health_router
from app.api.v1.routers.meals import router as meal_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(meal_router)
