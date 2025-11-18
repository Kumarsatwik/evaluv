from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .database import create_db_and_tables
from .config import settings
from .middleware.auth_middleware import AuthMiddleware, RateLimitMiddleware
from .routes.auth_routes import router as auth_router
from .routes.user_routes import router as user_router
from .routes.job_routes import router as job_router
from datetime import datetime, timezone

# ------------------------------------------
# Rate Limiter
# ------------------------------------------
limiter = Limiter(key_func=get_remote_address)


# ------------------------------------------
# Lifespan
# ------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_db_and_tables()
        print("Database initialized successfully.")
    except Exception as e:
        print("Database initialization failed:", e)
        raise e
    yield
    # Place for shutdown tasks if needed


# ------------------------------------------
# App Initialization
# ------------------------------------------
app = FastAPI(
    title="Secure Authentication API",
    description="A secure authentication and authorization system built with FastAPI",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()

@app.on_event("shutdown")
async def shutdown_event():
    pass


# Attach limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ------------------------------------------
# CORS Middleware
# ------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)


# ------------------------------------------
# Custom Middlewares
# Note: Order matters. Authentication should generally wrap business logic.
# ------------------------------------------
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)


# ------------------------------------------
# Routers
# ------------------------------------------
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(job_router)


# ------------------------------------------
# Routes
# ------------------------------------------
@app.get("/")
async def root():
    return {"message": "Secure Authentication API"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/protected")
async def protected_route():
    return {"message": "This is a protected route"}


@app.get("/admin-only")
async def admin_only_route():
    # Ideally enforce admin role here through AuthMiddleware or a dependency
    return {"message": "Admin access granted"}
