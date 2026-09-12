from fastapi import APIRouter

from app.api.routes import auth, farms, investor, iot_ai, notifications, researcher, verifier

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(farms.router)
api_router.include_router(verifier.router)
api_router.include_router(investor.router)
api_router.include_router(researcher.router)
api_router.include_router(notifications.router)
api_router.include_router(iot_ai.router)
