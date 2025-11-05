"""
Routes pour l'API
"""

from .files import router as files_router
from .folders import router as folders_router
from .static import router as static_router

__all__ = ['files_router', 'folders_router', 'static_router']

