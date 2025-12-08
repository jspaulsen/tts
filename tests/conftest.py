import os

from fastapi.testclient import TestClient
import pytest


os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost/postgres"
os.environ['ADMIN_API_TOKEN'] = "test_admin_key"


from src.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client
