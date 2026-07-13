"""
Aggregates every v1 endpoint router into one. main.py only needs to
import and include this single router.

When the next milestone adds jobs/companies endpoints, their routers
get included here too -- this file is the one place that maps
"/api/v1/<resource>" to its implementation.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()
api_router.include_router(auth.router)
