from fastapi import APIRouter

from app.api.routes import admin_homepage, homepage, status

api_router = APIRouter(prefix="/api")
api_router.include_router(homepage.router, tags=["homepage"])
api_router.include_router(status.router, tags=["status"])
api_router.include_router(admin_homepage.router, tags=["admin"])
