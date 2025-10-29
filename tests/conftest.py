import pytest
import os
import tempfile
from main import app
from app.models import db_manager


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'

    # Use temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE_URL'] = f'sqlite:///{db_path}'

    with app.test_client() as client:
        with app.app_context():
            # Initialize test database
            db_manager.init_database()
        yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def auth_token(client):
    """Get authentication token for testing"""
    # This would need to be implemented based on your auth system
    # For now, return a mock token
    return "test_auth_token"


@pytest.fixture
def sample_blog_data():
    """Sample blog post data for testing"""
    return {
        "keyword": "test SEO tools",
        "secondary_keywords": "SEO software, ranking tools"
    }


@pytest.fixture
def sample_gbp_data():
    """Sample GBP post data for testing"""
    return {
        "content": "Check out our latest services! We help businesses improve their online visibility.",
        "image_url": "https://example.com/image.jpg",
        "cta_url": "https://example.com"
    }