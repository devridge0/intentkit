"""API server module.

This module initializes and configures the FastAPI application,
including routers, middleware, and startup/shutdown events.

The API server provides endpoints for agent execution and management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin.api import admin_router
from app.admin.scheduler import start_scheduler
from app.config.config import config
from app.core.api import core_router
from app.entrypoints.web import chat_router
from app.services.twitter.oauth2 import router as twitter_oauth2_router
from app.services.twitter.oauth2_callback import router as twitter_callback_router
from models.db import init_db

# init logger
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    This context manager:
    1. Initializes database connection
    2. Performs any necessary startup tasks
    3. Handles graceful shutdown

    Args:
        app: FastAPI application instance
    """
    # Initialize database
    init_db(**config.db)

    # Start scheduler for periodic tasks
    scheduler = start_scheduler()

    logger.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(core_router)
app.include_router(twitter_callback_router)
app.include_router(twitter_oauth2_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Check API server health.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}
