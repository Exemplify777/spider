"""
API Routes

FastAPI route modules for the SPIDER web API.
"""

from . import auth, dashboard, monitoring, plugins, configuration, users, system

__all__ = [
    "auth",
    "dashboard", 
    "monitoring",
    "plugins",
    "configuration",
    "users",
    "system"
]
