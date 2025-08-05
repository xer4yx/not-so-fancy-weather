from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from version import __version__

from interfaces.api.routers import user_router, weather_router, auth_router, admin_router
from interfaces.api.di import get_migration_service
from utils.configs import NSFWSetting
from infrastructure.logger import get_logger, shutdown_logger


# Setup logger
logger = get_logger("main", "logs/app.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    """
    logger.info(f"NSFW API v{__version__} booting up", extra={"version": __version__})
    
    # Run user schema migration at startup
    try:
        migration_service = get_migration_service()
        migrated_count = migration_service.migrate_user_schema()
        logger.info(f"User schema migration completed: {migrated_count} users updated")
    except Exception as e:
        logger.error(f"Error during startup migration: {str(e)}", exc_info=True)
    
    yield
    logger.info("NSFW API shutting down")
    shutdown_logger()


basic_settings = NSFWSetting()
app = FastAPI(
    title=basic_settings.NAME,
    description="NotSoFancyWeather(NSFW) API",
    version=__version__,
    lifespan=lifespan,
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(weather_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get(path="/")
def get_root():
    logger.debug(f"Root endpoint called. Redirecting user to {basic_settings.REDIRECT_URL}")
    return RedirectResponse(url=basic_settings.REDIRECT_URL)


if __name__ == "__main__":
    logger.info(
        "Starting server",
        extra={
            "host": basic_settings.HOST,
            "port": basic_settings.PORT,
            "reload": basic_settings.RELOAD
        }
    )
    uvicorn.run(
        app="main:app",
        host=basic_settings.HOST,
        port=basic_settings.PORT,
        reload=basic_settings.RELOAD
    )    
