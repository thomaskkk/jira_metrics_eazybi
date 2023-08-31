import pytest
from src.main import create_app

@pytest.fixture(scope="module")
def app():
    return create_app()