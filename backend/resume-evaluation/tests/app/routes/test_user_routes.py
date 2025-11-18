import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.schemas.user import UserUpdateRequest, UserResponse
from unittest.mock import AsyncMock
from uuid import uuid4


class TestUserRoutes:
    """Test cases for user management routes"""

    def test_get_user_by_id_self(self, client, mock_user_controller):
        """Test get user by ID when user gets their own info"""
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
        mock_user_controller.get_user_by_id.return_value = expected_response

        response = client.get(f"/users/{user_id}", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "testuser"
        mock_user_controller.get_user_by_id.assert_called_once()

    def test_get_user_by_id_admin(self, client, mock_user_controller):
        """Test get user by ID as admin"""
        user_id = str(uuid4())
        admin_id = str(uuid4())
        expected_response = UserResponse(
            id=user_id,
            username="otheruser",
            email="other@example.com",
            full_name="Other User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_user_controller.get_user_by_id.return_value = expected_response

        response = client.get(f"/users/{user_id}", headers={
            "X-Test-User-Id": admin_id,
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        mock_user_controller.get_user_by_id.assert_called_once()

    def test_get_user_by_id_unauthorized(self, client, mock_user_controller):
        """Test get user by ID without permission (not self and not admin)"""
        user_id = str(uuid4())
        other_user_id = str(uuid4())

        from app.utils.exceptions import InsufficientPermissionsException
        mock_user_controller.get_user_by_id.side_effect = InsufficientPermissionsException()

        response = client.get(f"/users/{user_id}", headers={
            "X-Test-User-Id": other_user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403  # Forbidden

    def test_get_user_by_id_unauthenticated(self, client, mock_user_controller):
        """Test get user by ID when not authenticated"""
        user_id = str(uuid4())

        mock_user_controller.get_user_by_id.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.get(f"/users/{user_id}")

        assert response.status_code == 401

    def test_get_user_by_id_not_found(self, client, mock_user_controller):
        """Test get user by ID when user doesn't exist"""
        user_id = str(uuid4())

        from app.utils.exceptions import UserNotFoundException
        mock_user_controller.get_user_by_id.side_effect = UserNotFoundException()

        response = client.get(f"/users/{user_id}", headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 404

    def test_get_all_users_admin(self, client, mock_user_controller):
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
            ),
            UserResponse(
                id=str(uuid4()),
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                role="admin",
                is_active=True,
                is_verified=True,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            )
        ]
        mock_user_controller.get_all_users.return_value = users

        response = client.get("/users/", headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_all_users_not_admin(self, client, mock_user_controller):
        """Test get all users as non-admin"""
        from app.utils.exceptions import InsufficientPermissionsException
        mock_user_controller.get_all_users.side_effect = InsufficientPermissionsException()

        response = client.get("/users/", headers={
            "X-Test-User-Id": str(uuid4()),
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403

    def test_get_all_users_unauthenticated(self, client, mock_user_controller):
        """Test get all users when not authenticated"""
        mock_user_controller.get_all_users.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.get("/users/")

        assert response.status_code == 401

    def test_update_user_self(self, client, mock_user_controller):
        """Test update user by self"""
        user_id = str(uuid4())
        update_data = UserUpdateRequest(username="updatedname", email="updated@example.com")

        expected_response = UserResponse(
            id=user_id,
            username="updatedname",
            email="updated@example.com",
            full_name="Updated User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_user_controller.update_user.return_value = expected_response

        response = client.put(f"/users/{user_id}", json=update_data.model_dump(exclude_unset=True), headers={
            "X-Test-User-Id": user_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedname"
        mock_user_controller.update_user.assert_called_once()

    def test_update_user_admin(self, client, mock_user_controller):
        """Test update user as admin"""
        user_id = str(uuid4())
        admin_id = str(uuid4())
        update_data = UserUpdateRequest(username="updatedname")

        expected_response = UserResponse(
            id=user_id,
            username="updatedname",
            email="original@example.com",
            full_name="Original User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_user_controller.update_user.return_value = expected_response

        response = client.put(f"/users/{user_id}", json=update_data.model_dump(exclude_unset=True), headers={
            "X-Test-User-Id": admin_id,
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updatedname"

    def test_update_user_unauthorized(self, client, mock_user_controller):
        """Test update user without permission"""
        user_id = str(uuid4())
        other_id = str(uuid4())
        update_data = UserUpdateRequest(username="updatedname")

        from app.utils.exceptions import InsufficientPermissionsException
        mock_user_controller.update_user.side_effect = InsufficientPermissionsException()

        response = client.put(f"/users/{user_id}", json=update_data.model_dump(exclude_unset=True), headers={
            "X-Test-User-Id": other_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403

    def test_update_user_unauthenticated(self, client, mock_user_controller):
        """Test update user when not authenticated"""
        user_id = str(uuid4())
        update_data = UserUpdateRequest(username="updatedname")

        mock_user_controller.update_user.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.put(f"/users/{user_id}", json=update_data.model_dump(exclude_unset=True))

        assert response.status_code == 401

    def test_delete_user_admin(self, client, mock_user_controller):
        """Test delete user as admin"""
        user_id = str(uuid4())
        admin_id = str(uuid4())

        mock_user_controller.delete_user.return_value = {"message": "User deactivated successfully"}

        response = client.delete(f"/users/{user_id}", headers={
            "X-Test-User-Id": admin_id,
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        assert "deactivated successfully" in response.json()["message"]
        mock_user_controller.delete_user.assert_called_once()

    def test_delete_user_self_not_allowed(self, client, mock_user_controller):
        """Test delete self as admin (should not allow)"""
        user_id = str(uuid4())  # Same ID as authenticated user

        mock_user_controller.delete_user.side_effect = HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

        response = client.delete(f"/users/{user_id}", headers={
            "X-Test-User-Id": user_id,  # Trying to delete self
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 400
        assert "own account" in response.json()["detail"]

    def test_delete_user_unauthorized(self, client, mock_user_controller):
        """Test delete user as non-admin"""
        user_id = str(uuid4())
        other_id = str(uuid4())

        from app.utils.exceptions import InsufficientPermissionsException
        mock_user_controller.delete_user.side_effect = InsufficientPermissionsException()

        response = client.delete(f"/users/{user_id}", headers={
            "X-Test-User-Id": other_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403

    def test_activate_user_admin(self, client, mock_user_controller):
        """Test activate user as admin"""
        user_id = str(uuid4())
        admin_id = str(uuid4())

        expected_response = UserResponse(
            id=user_id,
            username="user",
            email="user@example.com",
            full_name="Activated User",
            role="user",
            is_active=True,
            is_verified=True,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_user_controller.activate_user.return_value = expected_response

        response = client.post(f"/users/{user_id}/activate", headers={
            "X-Test-User-Id": admin_id,
            "X-Test-User-Role": "admin"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True
        mock_user_controller.activate_user.assert_called_once()

    def test_activate_user_unauthorized(self, client, mock_user_controller):
        """Test activate user as non-admin"""
        user_id = str(uuid4())
        other_id = str(uuid4())

        from app.utils.exceptions import InsufficientPermissionsException
        mock_user_controller.activate_user.side_effect = InsufficientPermissionsException()

        response = client.post(f"/users/{user_id}/activate", headers={
            "X-Test-User-Id": other_id,
            "X-Test-User-Role": "user"
        })

        assert response.status_code == 403

    def test_activate_user_unauthenticated(self, client, mock_user_controller):
        """Test activate user when not authenticated"""
        user_id = str(uuid4())

        mock_user_controller.activate_user.side_effect = HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

        response = client.post(f"/users/{user_id}/activate")

        assert response.status_code == 401
