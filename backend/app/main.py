"""FastAPI Application Entry Point"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1 import auth, employee_portal, employees, health, payroll
from app.core.config import get_config
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    PayrollError,
    ValidationError,
)
from app.core.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    config = get_config()
    logger.info(f"Starting {config.app_name} v{__version__}")
    logger.info(f"Debug mode: {config.debug}")

    # Initialize Supabase client
    SupabaseClient.get_client()
    logger.info("Supabase client initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    config = get_config()

    app = FastAPI(
        title="BeanFlow Payroll API",
        description="Canadian Payroll Management System",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if config.debug else None,
        redoc_url="/redoc" if config.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": exc.message, "details": exc.details},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": exc.message, "details": exc.details},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": exc.message, "details": exc.details},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": exc.message, "details": exc.details},
        )

    @app.exception_handler(PayrollError)
    async def payroll_error_handler(request: Request, exc: PayrollError):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "details": exc.details},
        )

    # Register routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(payroll.router, prefix="/api/v1/payroll", tags=["Payroll"])
    app.include_router(employees.router, prefix="/api/v1/employees", tags=["Employees"])
    app.include_router(employee_portal.router, prefix="/api/v1", tags=["Employee Portal"])

    return app


# Create application instance
app = create_app()
