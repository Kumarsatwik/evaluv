from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from .database import create_db_and_tables
from .config import settings
from .middleware.auth_middleware import AuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .utils.redis_client import redis_client
from .utils.qdrant_client import qdrant_client
from .routes.auth_routes import router as auth_router
from .routes.user_routes import router as user_router
from .routes.job_routes import router as job_router
from .routes.resume_routes import router as resume_router
from datetime import datetime, timezone

# ------------------------------------------
# Lifespan
# ------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await create_db_and_tables()
        print("Database initialized successfully.")
    except Exception as e:
        print("Database initialization failed:", e)
        raise e

    try:
        await redis_client.connect()
        redis_connected = await redis_client.ping()
        if redis_connected:
            print("Redis connected successfully.")
        else:
            print("Warning: Redis connection test failed.")
    except Exception as e:
        print("Redis initialization failed:", e)
        # Continue without Redis (graceful degradation)

    try:
        await qdrant_client.connect()
        qdrant_healthy = qdrant_client.health_check()
        if qdrant_healthy:
            print("Qdrant connected successfully.")
        else:
            print("Warning: Qdrant health check failed.")
    except Exception as e:
        print("Qdrant initialization failed:", e)
        # Continue without Qdrant (graceful degradation)

    yield

    # Shutdown
    try:
        await redis_client.disconnect()
        print("Redis disconnected successfully.")
    except Exception as e:
        print("Redis disconnection error:", e)


# ------------------------------------------
# App Initialization
# ------------------------------------------
app = FastAPI(
    title="Secure Authentication API",
    description="A secure authentication and authorization system built with FastAPI",
    version="1.0.0",
)

# ------------------------------------------
# OpenAPI Security Configuration
# ------------------------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [
        {"BearerAuth": []}
    ]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi

@app.on_event("startup")
async def startup_event():
    # await create_db_and_tables()
    pass

@app.on_event("shutdown")
async def shutdown_event():
    pass


# Removed - using dedicated rate limiting middleware now


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
app.include_router(resume_router)


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
