"""
Payroll API Router Package

Composes sub-routers for payroll endpoints.
All endpoints are mounted under /api/v1/payroll prefix (set in main.py).
"""

from fastapi import APIRouter

from .calculation import router as calculation_router
from .config import router as config_router
from .paystubs import router as paystubs_router
from .runs import router as runs_router
from .sick_leave import router as sick_leave_router

# Create main payroll router
router = APIRouter()

# Include all sub-routers with NO prefix (prefix is already /api/v1/payroll in main.py)
router.include_router(calculation_router, tags=["Payroll Calculation"])
router.include_router(config_router, tags=["Payroll Config"])
router.include_router(runs_router, tags=["Payroll Runs"])
router.include_router(paystubs_router, tags=["Paystubs"])
router.include_router(sick_leave_router, tags=["Sick Leave"])

# Export router for main.py import
__all__ = ["router"]
