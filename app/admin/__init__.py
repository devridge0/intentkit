from app.admin.api import admin_router, admin_router_readonly
from app.admin.health import health_router
from app.admin.schema import schema_router_readonly

__all__ = [
    "admin_router",
    "admin_router_readonly",
    "health_router",
    "schema_router_readonly",
]
