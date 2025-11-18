import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.schemas.user import UserCreateRequest, UserLoginRequest, UserResponse
from app.schemas.auth import RefreshTokenRequest, TokenBlacklistRequest, ChangePasswordRequest
from unittest.mock import AsyncMock
from uuid import uuid4


class TestAuthRoutes:
    """Test cases for authentication routes"""

    def test_register_success(self, client, mock_auth_controller):
        """Test successful user registration"""
        user_data = UserCreateRequest(
            username="testuser",
            email="test@example.com",
            password="StrongPass123!",
            role="user"
        )

        expected_response = UserResponse(
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

        mock_auth_controller.register.return_value = expected_response

        response = client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        mock_auth_controller.register.assert_called_once_with(user_data)

    def test_register_duplicate_user(self, client, mock_auth_controller):
        """Test registration with duplicate user"""
        user_data = UserCreateRequest(
            username="existinguser",
            email="existing@example.com",
            password="StrongPass123!",
            role="user"
        )

        mock_auth_controller.register.side_effect = HTTPException(
            status_code=409,
            detail="User with this email or username already exists"
        )

        response = client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_register_weak_password(self, client, mock_auth_controller):
        """Test registration with weak password"""
        user_data = UserCreateRequest(
            username="testuser",
            email="test@example.com",
            password="weak",
            role="user"
        )

        mock_auth_controller.register.side_effect = HTTPException(
            status_code=400,
            detail="Password does not meet security requirements"
        )

        response = client.post("/auth/register", json=user_data.model_dump())

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_login_success(self, client, mock_auth_controller):
        """Test successful login"""
        login_data = UserLoginRequest(
            username="testuser",
            password="password123"
        )

        mock_auth_controller.login.return_value = {
            "access_token": "token123",
            "refresh_token": "refresh123",
            "expires_in": 3600
        }

        response = client.post("/auth/login", json=login_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        mock_auth_controller.login.assert_called_once_with(login_data)

    def test_login_invalid_credentials(self, client, mock_auth_controller):
        """Test login with invalid credentials"""
        from app.utils.exceptions import InvalidCredentialsException

        login_data = UserLoginRequest(
            username="testuser",
            password="wrongpassword"
        )

        mock_auth_controller.login.side_effect = InvalidCredentialsException()

        response = client.post("/auth/login", json=login_data.model_dump())

        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    def test_refresh_token_success(self, client, mock_auth_controller):
        """Test successful token refresh"""
        refresh_data = RefreshTokenRequest(refresh_token="valid_refresh_token")

        mock_auth_controller.refresh_token.return_value = {
            "access_token": "new_token123",
            "refresh_token": "new_refresh123",
            "expires_in": 3600
        }

        response = client.post("/auth/refresh", json=refresh_data.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        mock_auth_controller.refresh_token.assert_called_once_with(refresh_data)

    def test_refresh_token_invalid(self, client, mock_auth_controller):
        """Test refresh with invalid token"""
        from app.utils.exceptions import InvalidCredentialsException

        refresh_data = RefreshTokenRequest(refresh_token="invalid_token")

        mock_auth_controller.refresh_token.side_effect = InvalidCredentialsException()

        response = client.post("/auth/refresh", json=refresh_data.model_dump())

        assert response.status_code == 401

    def test_logout_success(self, client, mock_auth_controller):
        """Test successful logout"""
        logout_data = TokenBlacklistRequest(token="access_token")

        mock_auth_controller.logout.return_value = {"message": "Successfully logged out"}

        response = client.post("/auth/logout", json=logout_data.model_dump())

        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
        mock_auth_controller.logout.assert_called_once()
        # Note: We can't easily check the request parameter in this test setup

    def test_get_current_user_authenticated(self, client, mock_auth_controller):
        """Test get current user when authenticated"""
        user_id = str(uuid4())
        expected_response = UserResponse(
            id=user_id,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_auth_controller.get_current_user.return_value = expected_response

        response = client.get("/auth/me", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

        # Verify the controller was called with the request that has state.user set
        mock_auth_controller.get_current_user.assert_called_once()
        call_args = mock_auth_controller.get_current_user.call_args
        request_arg = call_args[0][0]  # First positional argument
        assert hasattr(request_arg.state, 'user')
        assert request_arg.state.user["id"] == user_id

    def test_get_current_user_unauthenticated(self, client, mock_auth_controller):
        """Test get current user when not authenticated"""
        mock_auth_controller.get_current_user.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.get("/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_update_current_user_success(self, client, mock_auth_controller):
        """Test update current user info"""
        user_id = str(uuid4())
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }

        expected_response = UserResponse(
            id=user_id,
            username="updateduser",
            email="updated@example.com",
            full_name="Updated User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_auth_controller.update_current_user.return_value = expected_response

        response = client.put("/auth/me", json=update_data, headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"

    def test_update_current_user_unauthenticated(self, client, mock_auth_controller):
        """Test update current user when not authenticated"""
        update_data = {"username": "updateduser"}

        mock_auth_controller.update_current_user.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.put("/auth/me", json=update_data)

        assert response.status_code == 401

    def test_change_password_success(self, client, mock_auth_controller):
        """Test successful password change"""
        change_data = ChangePasswordRequest(
            old_password="oldpass123",
            new_password="NewStrongPass123!"
        )

        mock_auth_controller.change_password.return_value = {"message": "Password changed successfully"}

        response = client.post("/auth/change-password", json=change_data.model_dump(), headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        assert "changed successfully" in response.json()["message"]

    def test_change_password_wrong_old_password(self, client, mock_auth_controller):
        """Test password change with wrong old password"""
        change_data = ChangePasswordRequest(
            old_password="wrongoldpass",
            new_password="NewStrongPass123!"
        )

        mock_auth_controller.change_password.side_effect = HTTPException(
            status_code=400,
            detail="Old password is incorrect"
        )

        response = client.post("/auth/change-password", json=change_data.model_dump(), headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 400

    def test_get_all_users_admin(self, client, mock_auth_controller):
        """Test get all users as admin"""
        users = [
            UserResponse(
                id=str(uuid4()),
                username="user1",
                email="user1@example.com",
                full_name="User One",
                role="user",
                is_active=True,
                is_verified=True,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            ),
            UserResponse(
                id=str(uuid4()),
                username="user2",
                email="user2@example.com",
                full_name="User Two",
                role="user",
                is_active=True,
                is_verified=True,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
        ]
        mock_auth_controller.get_all_users.return_value = users

        response = client.get("/auth/admin/users", headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(user["role"] == "user" for user in data)

    def test_get_all_users_not_admin(self, client, mock_auth_controller):
        """Test get all users as non-admin"""
        from app.utils.exceptions import InsufficientPermissionsException

        mock_auth_controller.get_all_users.side_effect = InsufficientPermissionsException()

        response = client.get("/auth/admin/users", headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403  # Forbidden
