import pytest
import responses
from app import create_app
from app.conf_test import cfg


@pytest.fixture
def resp():
    with responses.RequestsMock() as r:
        yield r


@pytest.fixture
def app():
    yield create_app(cfg)
