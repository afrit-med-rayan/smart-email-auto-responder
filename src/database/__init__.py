"""
Database package initialization.
"""

from src.database.models import Base, Email, Classification, Draft, ProcessingMetadata
from src.database.connection import (
    engine,
    AsyncSessionLocal,
    get_db,
    init_db,
    drop_db,
    check_db_health,
    close_db,
)

__all__ = [
    "Base",
    "Email",
    "Classification",
    "Draft",
    "ProcessingMetadata",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "drop_db",
    "check_db_health",
    "close_db",
]
