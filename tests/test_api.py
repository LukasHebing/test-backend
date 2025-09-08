import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from src.test_backend.api import app, hash_password

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.query = MagicMock()
    return db

def test_register_success(client, mocker, mock_db):
    mocker.patch("src.test_backend.api.get_db", return_value=mock_db)
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "secret"})
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}
    assert mock_db.add.called

def test_login_success(client, mocker, mock_db):
    class DummyUser:
        email = "test@example.com"