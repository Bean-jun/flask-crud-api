from models import HTTPModel
from flask_crud_api.view import CommonView, CommonDetailView
from flask_crud_api.router import action


class HTTPModelView(CommonView):
    view_filter_fields = (
        ("method", "="),
        ("path", "regexp"),
    )

    def __init__(self):
        super().__init__(HTTPModel)


class HTTPModelDetailView(CommonDetailView):
    def __init__(self):
        super().__init__(HTTPModel)
