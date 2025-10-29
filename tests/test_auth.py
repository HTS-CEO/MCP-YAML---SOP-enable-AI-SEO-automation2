import pytest
from app.models import user_manager


def test_user_registration():
    """Test user registration functionality"""
    result = user_manager.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )

    assert 'error' not in result
    assert result['success'] is True
    assert 'user_id' in result


def test_user_authentication():
    """Test user login functionality"""
    # First create a user
    user_manager.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123"
    )

    # Test authentication
    result = user_manager.authenticate_user("testuser2", "testpass123")

    assert 'error' not in result
    assert result['success'] is True
    assert result['user']['username'] == "testuser2"


def test_invalid_login():
    """Test invalid login attempts"""
    result = user_manager.authenticate_user("nonexistent", "wrongpass")

    assert 'error' in result
    assert result['error'] == "User not found"


def test_duplicate_user():
    """Test duplicate user creation"""
    # Create first user
    user_manager.create_user(
        username="duplicate",
        email="dup@example.com",
        password="testpass123"
    )

    # Try to create duplicate
    result = user_manager.create_user(
        username="duplicate",
        email="dup2@example.com",
        password="testpass123"
    )

    assert 'error' in result
    assert 'already exists' in result['error']


def test_password_validation():
    """Test password validation"""
    result = user_manager.authenticate_user("testuser2", "wrongpassword")

    assert 'error' in result
    assert result['error'] == "Invalid password"