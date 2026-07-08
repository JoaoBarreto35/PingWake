from fastapi import APIRouter

from app.api.routes import checks, health, incidents, integrations, internal, notifications, targets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(targets.router)
api_router.include_router(checks.router)
api_router.include_router(incidents.router)
api_router.include_router(notifications.router)
api_router.include_router(integrations.router)
api_router.include_router(internal.router)
