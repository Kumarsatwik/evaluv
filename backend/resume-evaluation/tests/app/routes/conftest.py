import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from unittest.mock import AsyncMock, MagicMock
from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.job_routes import router as job_router
from app.controllers.auth_controller import AuthController
from app.controllers.user_controller import UserController
from app.controllers.job_controller import JobController
from fastapi import FastAPI
from app.schemas.user import UserResponse
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware


class TestAuthMiddleware(BaseHTTPMiddleware):
    """Test middleware to set request.state.user based on custom headers"""
    async def dispatch(self, request: Request, call_next):
        # Check for test auth headers
        user_id = request.headers.get("X-Test-User-Id")
        role = request.headers.get("X-Test-User-Role", "user")
        sub = request.headers.get("X-Test-User-Sub", "test@example.com")

        if user_id:  # If test user headers present, set state
            request.state.user = {
                "id": user_id,
                "role": role,
                "sub": sub
            }

        response = await call_next(request)
        return response


@pytest.fixture
def mock_auth_controller():
    """Mock AuthController for testing"""
    controller = MagicMock(spec=AuthController)
    # Set up async mocks
    controller.register = AsyncMock()
    controller.login = AsyncMock()
    controller.refresh_token = AsyncMock()
    controller.logout = AsyncMock()
    controller.get_current_user = AsyncMock()
    controller.update_current_user = AsyncMock()
    controller.change_password = AsyncMock()
    controller.get_all_users = AsyncMock()
    return controller


@pytest.fixture
def mock_user_controller():
    """Mock UserController for testing"""
    controller = MagicMock(spec=UserController)
    # Set up async mocks
    controller.get_user_by_id = AsyncMock()
    controller.get_all_users = AsyncMock()
    controller.update_user = AsyncMock()
    controller.delete_user = AsyncMock()
    controller.activate_user = AsyncMock()
    return controller


@pytest.fixture
def mock_job_controller():
    """Mock JobController for testing"""
    controller = MagicMock(spec=JobController)
    # Set up async mocks
    controller.create_job = AsyncMock()
    controller.get_job_by_id = AsyncMock()
    controller.get_my_jobs = AsyncMock()
    controller.get_all_jobs = AsyncMock()
    controller.update_job = AsyncMock()
    controller.delete_job = AsyncMock()
    return controller


@pytest.fixture
def test_app(mock_auth_controller, mock_user_controller):
    """Create test FastAPI app with test middleware and overridden dependencies"""
    from app.routes.auth_routes import get_auth_controller
    from app.routes.user_routes import get_user_controller

    app = FastAPI()
    app.add_middleware(TestAuthMiddleware)
    app.include_router(auth_router)
    app.include_router(user_router)

    # Override dependencies
    app.dependency_overrides[get_auth_controller] = lambda: mock_auth_controller
    app.dependency_overrides[get_user_controller] = lambda: mock_user_controller

    return app


@pytest.fixture
def test_app_jobs(mock_auth_controller, mock_user_controller, mock_job_controller):
    """Create test FastAPI app with job routes and test middleware"""
    from app.routes.auth_routes import get_auth_controller
    from app.routes.user_routes import get_user_controller
    from app.routes.job_routes import get_job_controller

    app = FastAPI()
    app.add_middleware(TestAuthMiddleware)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(job_router)

    # Override dependencies
    app.dependency_overrides[get_auth_controller] = lambda: mock_auth_controller
    app.dependency_overrides[get_user_controller] = lambda: mock_user_controller
    app.dependency_overrides[get_job_controller] = lambda: mock_job_controller

    return app


@pytest.fixture
def client(test_app):
    """Test client for making requests"""
    return TestClient(test_app)


@pytest.fixture
def client_jobs(test_app_jobs):
    """Test client for job route requests"""
    return TestClient(test_app_jobs)


@pytest.fixture
def authenticated_request():
    """Create a mock request with authenticated user"""
    request = MagicMock(spec=Request)
    request.state.user = {
        "id": str(uuid4()),
        "role": "user",
        "sub": "test@example.com"
    }
    return request


@pytest.fixture
def admin_request():
    """Create a mock request with admin user"""
    request = MagicMock(spec=Request)
    request.state.user = {
        "id": str(uuid4()),
        "role": "admin",
        "sub": "admin@example.com"
    }
    return request


@pytest.fixture
def auth_controller_with_user(mock_auth_controller, authenticated_request):
    """AuthController mock configured for authenticated user"""
    mock_auth_controller.get_current_user = AsyncMock(return_value=UserResponse(
        id=authenticated_request.state.user["id"],
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role="user",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    ))
    mock_auth_controller.update_current_user = AsyncMock(return_value=UserResponse(
        id=authenticated_request.state.user["id"],
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_verified=True,
        role="user",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    ))
    mock_auth_controller.change_password = AsyncMock(return_value={"message": "Password changed successfully"})
    mock_auth_controller.get_all_users = AsyncMock(return_value=[UserResponse(
        id=str(uuid4()),
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        role="admin",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )])
    return mock_auth_controller, authenticated_request


@pytest.fixture
def auth_controller_admin(mock_auth_controller, admin_request):
    """AuthController mock configured for admin user"""
    mock_auth_controller.get_all_users = AsyncMock(return_value=[
        UserResponse(
            id=str(uuid4()),
            username="user1",
            email="user1@example.com",
            full_name="User One",
            is_active=True,
            is_verified=True,
            role="user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        ),
        UserResponse(
            id=str(uuid4()),
            username="user2",
            email="user2@example.com",
            full_name="User Two",
            is_active=True,
            is_verified=True,
            role="user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
    ])
    return mock_auth_controller, admin_request


@pytest.fixture
def user_controller_with_user(mock_user_controller, authenticated_request, admin_request):
    """UserController mock configured for various scenarios"""
    user_response = UserResponse(
        id=str(uuid4()),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True,
        is_verified=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    admin_response = UserResponse(
        id=str(uuid4()),
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True,
        is_verified=True,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )

    # Get user by id - admin or self
    mock_user_controller.get_user_by_id = AsyncMock(
        side_effect=lambda user_id, request: user_response if str(user_id) == authenticated_request.state.user["id"] or request.state.user["role"] == "admin" else None
    )

    # Update user - admin or self
    mock_user_controller.update_user = AsyncMock(return_value=user_response)

    # Get all users - admin only
    mock_user_controller.get_all_users = AsyncMock(return_value=[user_response, admin_response])

    # Delete user - admin only, not self
    mock_user_controller.delete_user = AsyncMock(return_value={"message": "User deactivated successfully"})

    # Activate user - admin only
    mock_user_controller.activate_user = AsyncMock(return_value=user_response)

    return mock_user_controller, authenticated_request, admin_request
