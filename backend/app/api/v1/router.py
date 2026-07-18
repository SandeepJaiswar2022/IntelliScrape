"""
Aggregates every v1 endpoint router into one. main.py only needs to
import and include this single router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, jobs

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(jobs.router)
