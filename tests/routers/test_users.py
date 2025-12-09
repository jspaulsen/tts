import uuid

import pytest
from fastapi.testclient import TestClient

from src.configuration import Configuration


class TestUserRoutes:
    @pytest.fixture
    def auth_headers(self) -> dict[str, str]:
        config = Configuration.get()
        return {"Authorization": f"Bearer {config.admin_api_token.get_secret_value()}"}

    def test_get_users_unauthorized(self, client: TestClient):
        """Test that GET /users returns 401 without auth."""
        response = client.get("/users/")
        assert response.status_code == 401

    def test_get_users_invalid_token(self, client: TestClient):
        """Test that GET /users returns 401 with invalid token."""
        response = client.get(
            "/users/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_get_users(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that GET /users returns a list of users."""
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_user(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that POST /users creates a new user."""
        username = f"test-user-{uuid.uuid4()}"
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={"username": username},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == username
        assert "id" in data

    def test_create_user_unauthorized(self, client: TestClient):
        """Test that POST /users returns 401 without auth."""
        username = f"test-user-{uuid.uuid4()}"
        response = client.post(
            "/users/",
            json={"username": username},
        )
        assert response.status_code == 401

    def test_create_user_duplicate(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that POST /users returns 409 for duplicate username."""
        username = f"test-user-{uuid.uuid4()}"

        # Create user first time
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={"username": username},
        )
        assert response.status_code == 200

        # Try to create same user again
        response = client.post(
            "/users/",
            headers=auth_headers,
            json={"username": username},
        )
        assert response.status_code == 409

    def test_created_user_appears_in_list(self, client: TestClient, auth_headers: dict[str, str]):
        """Test that a created user appears in the users list."""
        username = f"test-user-{uuid.uuid4()}"

        # Create user
        create_response = client.post(
            "/users/",
            headers=auth_headers,
            json={"username": username},
        )
        assert create_response.status_code == 200

        # Get users list
        list_response = client.get("/users/", headers=auth_headers)
        assert list_response.status_code == 200
        users = list_response.json()

        # Check user is in list
        usernames = [u["username"] for u in users]
        assert username in usernames
