import json
import pytest
from flask import Blueprint, Flask
from flask.testing import FlaskClient

from models import Book


@pytest.fixture
def api(app: Flask):
    from flask_crud_api.router import Router
    from flask_crud_api.view import CommonView
    from flask_crud_api.router import action
    from flask_crud_api.decorator import swagger

    bp = Blueprint("v1", __name__, url_prefix="/api")
    router = Router(bp)

    @swagger(
        tags=["书本API"],
        summary="图书接口API",
        description="这是一个图书模型的接口API",
        login_required=True,
    )
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
def open_api(api, client: FlaskClient):
    response = client.get("/_docs/openapi.json")
    return response


def test_swagger(open_api):
    assert open_api.status_code == 200


def test_swagger_paths(open_api):

    assert open_api.status_code == 200
    data = json.loads(open_api.data)
    assert "/api/book" in data["paths"]
    assert "get" in data["paths"]["/api/book"]

    assert data["paths"]["/api/book"]["get"]["summary"] == "图书接口API"

    assert "post" in data["paths"]["/api/book"]
    assert data["paths"]["/api/book"]["post"]["summary"] == "图书接口API"
