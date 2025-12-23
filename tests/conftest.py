import os
import tempfile

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret",
    }
    app = create_app(config_override=config)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
