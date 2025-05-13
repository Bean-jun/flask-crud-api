from flask import Blueprint, Flask
from flask_crud_api.router import Router


def init_app(app: Flask):

    bp = Blueprint("v1", __name__, url_prefix="/api")
    router = Router(bp)

    from .api import (
        HTTPModelView,
        HTTPModelDetailView,
    )

    router.add_url_rule("/http", view_cls=HTTPModelView)
    router.add_url_rule(
        "/http/<int:pk>",
        view_cls=HTTPModelDetailView,
    )
    app.register_blueprint(bp)
