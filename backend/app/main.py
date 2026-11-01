from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("campuspilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting %s in %s mode...", settings.app_name, settings.app_env)
    if not settings.gemini_api_key:
        logger.warning("WARNING: GEMINI_API_KEY is not configured in backend/.env!")
    else:
        logger.info("Gemini configured with default model: %s", settings.gemini_model)
    yield
    logger.info("Shutting down %s...", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="CampusPilot AI - Campus Assistant & Student Navigation Platform",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes under /api
    app.include_router(api_router, prefix="/api")

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs_url": "/docs",
            "health_url": "/api/chat/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
