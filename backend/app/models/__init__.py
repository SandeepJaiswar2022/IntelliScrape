"""
Importing every model here ensures that anything importing
`app.models` (including Alembic's env.py) registers all tables on
`Base.metadata` -- otherwise `alembic revision --autogenerate` would
silently miss tables that were never imported anywhere.
"""

from app.models.user import User
from app.models.refresh_token import RefreshToken

__all__ = ["User", "RefreshToken"]
