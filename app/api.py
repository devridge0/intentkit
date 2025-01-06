"""IntentKit REST API Server.

This module implements the REST API for IntentKit, providing endpoints for:
- Chat
- Internal
- Admin
- Health monitoring
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.admin.api import admin_router
from app.admin.scheduler import start_scheduler
from app.config.config import config
from app.core.api import core_router
from app.entrypoints.web import chat_router
from app.models.db import init_db
from utils.logging import JsonFormatter

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
    # This part will run before the API server start
    # Initialize infrastructure
    init_db(**config.db)
    logger.info("API server start")
    scheduler = start_scheduler()
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(core_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Check API server health.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}
