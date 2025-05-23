import os
import sys

sys.path.insert(0, os.path.join(
    os.getcwd(),
    "src"
))

import pytest
from flask import Flask
from flask.testing import FlaskClient


from flask_crud_api.api import SimpleApi


@pytest.fixture
def app():
    app = Flask(__name__)
    # app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"
    app.config["FLASK_CRUD_API_DB_URL"] = 'sqlite:///:memory:'
    app.config["FLASK_CRUD_API_DB_DEBUG"] = True
    app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True
    SimpleApi(app)

    from models import create_tables
    from flask_crud_api.api import engine

    create_tables(engine)
    return app


@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()
