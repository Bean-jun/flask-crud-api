import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.getcwd()),
        "src",
    ),
)

from flask import Blueprint, Flask


from flask_crud_api.api import CrudApi
from flask_crud_api.router import Router, action
from flask_crud_api.view import CommonView
from flask_crud_api.decorator import swagger, Swagger
from flask_crud_api.openapi import BodyParam, QueryParam

app = Flask(__name__)
# app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"
app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///:memory:"
app.config["FLASK_CRUD_API_DB_DEBUG"] = True
app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True
CrudApi(app)
from models import Book, create_tables
from flask_crud_api.api import engine

create_tables(engine)


from test_view import _init_data

_init_data(app)


bp = Blueprint("v1", __name__, url_prefix="/api")
router = Router(bp)


@Swagger(
    parameters=[QueryParam("name", "书名过滤")],
    requestBody=[
        BodyParam("name", "书本名称", "月亮与六便士"),
        BodyParam("price", "书本价格", 12.9)
    ],
    auto_find_body=True,
    auto_find_params=True
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


if __name__ == "__main__":
    app.run(port=7256)
