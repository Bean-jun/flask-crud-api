import datetime
import json
import pytest
from flask import Blueprint, Flask, request
from werkzeug.security import generate_password_hash
from flask.testing import FlaskClient

from models import User, Book

def _init_data(app: Flask):
    with app.app_context():

        from flask_crud_api.api import session_factory

        session = session_factory()

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

@pytest.fixture
def init_data(app: Flask):
    _init_data(app)

@pytest.fixture
def book_by_commonview_api(app: Flask, init_data):
    from flask_crud_api.router import Router
    from flask_crud_api.view import CommonView
    from flask_crud_api.router import action

    bp = Blueprint("v1", __name__, url_prefix="/api")
    router = Router(bp)

    class BookView(CommonView):
        model = Book

        view_order_fields = (
            ("__order_pk", "desc"),
            ("__order_publish", "desc"),
        )
        view_filter_fields = (
            ("name", "regexp"),
            ("publish", "between"),
        )

        @action()
        def last(self, *args, **kwargs):
            stmt = self.get_queryset()
            stmt = stmt.order_by(self.model.pk.desc()).limit(1)
            result = self.orm.execute_one_or_none(stmt)
            return self.to_serializer(result, 1)

    router.add_url_rule("/book", view_cls=BookView)
    app.register_blueprint(bp)


@pytest.fixture
def book_by_commondetailview_api(app: Flask, init_data):
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


def test_base_index(app: Flask, client: FlaskClient):

    @app.route("/", methods=["GET", "POST"])
    def index():
        return request.method

    assert client.get("/").data == b"GET"
    assert client.post("/").data == b"POST"
    assert client.put("/").status_code == 405


def test_common_view_get(book_by_commonview_api, client: FlaskClient):
    response = client.get("/api/book")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["count"] in {4, 5}

def test_common_view_get_by_order(book_by_commonview_api, client: FlaskClient):
    response = client.get("/api/book?__order_pk=desc")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["result"][0]["pk"] != 1


def test_common_view_get_by_filter_name(book_by_commonview_api, client: FlaskClient):
    response = client.get("/api/book?name=书本0")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200

def test_common_view_get_by_filter_publish(book_by_commonview_api, client: FlaskClient):
    response = client.get("/api/book?publish=2025-05-23 12:00:00,2025-05-23 17:00:00")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200


def test_common_view_post(book_by_commonview_api, client: FlaskClient):
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


def test_common_view_action_get(book_by_commonview_api, client: FlaskClient):
    response = client.get("/api/book/last")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["count"] == 1


def test_common_view_detail_get(book_by_commondetailview_api, client: FlaskClient):
    response = client.get("/api/book/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200


def test_common_view_detail_post(book_by_commondetailview_api, client: FlaskClient):
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


def test_common_view_detail_put(book_by_commondetailview_api, client: FlaskClient):
    response = client.put(
        "/api/book/1",
        data={
            "name": "书本-新-新",
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
    assert data["data"]["result"][0]["name"] == "书本-新-新"


def test_common_view_detail_delete(book_by_commondetailview_api, client: FlaskClient):
    response = client.delete("/api/book/1")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["code"] == 200
