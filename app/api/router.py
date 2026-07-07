from fastapi import APIRouter

from app.api.routes import checks, health, incidents, internal, targets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(targets.router)
api_router.include_router(checks.router)
api_router.include_router(incidents.router)
api_router.include_router(internal.router)
