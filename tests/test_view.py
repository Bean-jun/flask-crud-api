import datetime
import json
import pytest
from flask import Blueprint, Flask, request
from werkzeug.security import generate_password_hash
from flask.testing import FlaskClient

from models import User, Book


@pytest.fixture
def init_data(app: Flask):
    with app.app_context():

        from flask_crud_api.orm import Orm
        from flask_crud_api.api import session_factory

        session = session_factory()

        orm = Orm()

        user_1 = User(username="user1", password=generate_password_hash("user1"))
        user_2 = User(username="user2", password=generate_password_hash("user2"))

        session.add_all([user_1, user_2])
        session.commit()
        session.refresh(user_1)

        books = [
            {
                "uid": user_1.pk,
                "name": "书本0",
                "publish": datetime.datetime.now(),
                "price": 10.2,
            },
            {
                "uid": user_1.pk,
                "name": "书本1",
                "publish": datetime.datetime.now(),
                "price": 11.2,
            },
            {
                "uid": user_1.pk,
                "name": "书本2",
                "publish": datetime.datetime.now(),
                "price": 3.2,
            },
            {
                "uid": user_1.pk,
                "name": "书本3",
                "publish": datetime.datetime.now(),
                "price": 7.2,
            },
        ]
        for book in books:
            _book = Book(**book)
            session.add(_book)
            session.commit()


def test_base_index(app: Flask, client: FlaskClient):

    @app.route("/", methods=["GET", "POST"])
    def index():
        return request.method

    assert client.get("/").data == b"GET"
    assert client.post("/").data == b"POST"
    assert client.put("/").status_code == 405


def test_book_by_commonview_api(app: Flask, client: FlaskClient, init_data):
    from flask_crud_api.router import Router
    from flask_crud_api.view import CommonView

    bp = Blueprint("v1", __name__, url_prefix="/api")
    router = Router(bp)

    class BookView(CommonView):
        model = Book

    router.add_url_rule("/book", view_cls=BookView)
    app.register_blueprint(bp)

    response = client.get("/api/book")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["count"] == 4

    response = client.post(
        "/api/book",
        data={
            "name": "创建新书",
            "publish": "2025-12-10 12:00:00",
            "price": 12.0,
            "uid": 2,
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200

    response = client.get("/api/book")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["count"] == 5


def test_book_by_commondetailview_api(app: Flask, client: FlaskClient, init_data):
    from flask_crud_api.router import Router
    from flask_crud_api.view import CommonDetailView

    bp = Blueprint("v1", __name__, url_prefix="/api")
    router = Router(bp)

    class BookDetailView(CommonDetailView):
        model = Book

    router.add_url_rule(
        "/book/<int:pk>",
        view_cls=BookDetailView,
    )
    app.register_blueprint(bp)

    response = client.get("/api/book/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200

    response = client.post(
        "/api/book/1",
        data={
            "name": "书本-新",
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["result"][0]["name"] == "书本-新"

    response = client.delete("/api/book/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
