"""API server module.

This module initializes and configures the FastAPI application,
including routers, middleware, and startup/shutdown events.

The API server provides endpoints for agent execution and management.
"""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.admin import (
    admin_router,
    admin_router_readonly,
    health_router,
    schema_router_readonly,
)
from app.config.config import config
from app.core.api import core_router
from app.entrypoints.web import chat_router, chat_router_readonly
from app.services.twitter.oauth2 import router as twitter_oauth2_router
from app.services.twitter.oauth2_callback import router as twitter_callback_router
from models.db import init_db

# init logger
logger = logging.getLogger(__name__)

if config.sentry_dsn:
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        sample_rate=config.sentry_sample_rate,
        traces_sample_rate=config.sentry_traces_sample_rate,
        profiles_sample_rate=config.sentry_profiles_sample_rate,
        environment=config.env,
        release=config.release,
        server_name="intent-api",
    )


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
    await init_db(**config.db)

    logger.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")


app = FastAPI(lifespan=lifespan)


@app.exception_handler(StarletteHTTPException)
async def global_exception_handler(request, exc):
    """Log all 500 errors at ERROR level"""
    if exc.status_code == 500:
        logger.error(f"Internal Server Error for request {request.url}: {str(exc)}")
    return await http_exception_handler(request, exc)


app.include_router(chat_router)
app.include_router(chat_router_readonly)
app.include_router(admin_router)
app.include_router(admin_router_readonly)
app.include_router(schema_router_readonly)
app.include_router(core_router)
app.include_router(twitter_callback_router)
app.include_router(twitter_oauth2_router)
app.include_router(health_router)
