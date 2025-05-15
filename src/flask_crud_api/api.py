import os
from flask import Blueprint, Flask, g
from flask.json.provider import DefaultJSONProvider

import dataclasses
import decimal
import uuid
from datetime import date
import datetime

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

engine: Engine

session_factory: Session


def _default(o):
    if isinstance(o, date):
        return datetime.datetime.strftime(o, "%Y-%m-%d %H:%M:%S")

    if isinstance(o, (decimal.Decimal, uuid.UUID)):
        return str(o)

    if dataclasses and dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)  # type: ignore[arg-type]

    if hasattr(o, "__html__"):
        return str(o.__html__())

    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


class InitializeRequest:

    def __init__(self, app: Flask):
        self.app = app
        self.app.before_request_funcs.setdefault(None, []).insert(
            0, self.before_request
        )
        self.app.teardown_request(self.teardown_request)

    def before_request(self):
        setattr(g, "session", session_factory())

    def teardown_request(self, exception):
        try:
            if hasattr(g, "session"):
                session = getattr(g, "session")
                if hasattr(session, "close"):
                    session.close()
                    del session
        except Exception as e:
            print(e)


class APIFlaskJSONProvider(DefaultJSONProvider):
    default = staticmethod(_default)


class CrudApi:

    def __init__(self, app=None):
        if app is None:
            return

        self.app = app
        self.init_app(self.app)

    def init_app(self, app: Flask):
        self.app = app
        app.json = APIFlaskJSONProvider(app)

        self.init_db_tools()
        self.init_hooks()
        self.init_api_docs()

    def init_db_tools(self):
        # sqlalchemy 兼容 flask_migrate
        global engine, session_factory
        from .models import Base, create_tables
        from flask_migrate import Migrate

        if "DB_URL" not in self.app.config:
            raise Exception("DB_URL NOT CONFIGURATION!")

        engine = create_engine(
            self.app.config["DB_URL"], echo=self.app.config.get("DB_DEBUG", False)
        )
        session_factory = sessionmaker(bind=engine)
        create_tables(engine)

        setattr(session_factory, "engine", engine)
        setattr(session_factory, "metadata", Base.metadata)
        Migrate().init_app(self.app, session_factory)

    def init_hooks(self):
        InitializeRequest(self.app)

    def init_api_docs(self):
        path = os.path.dirname(os.path.abspath(__file__))
        _api_docs = Blueprint(
            "_api_docs",
            __name__,
            static_folder=os.path.join(path, "static"),
            template_folder=os.path.join(path, "templates"),
            url_prefix="/_docs",
        )

        @_api_docs.get("/")
        def __index():
            from flask import render_template

            return render_template("index.html")

        @_api_docs.get("/openapi.json")
        def __openapi():
            from flask_crud_api._openapi import render_api
            return render_api(self.app)

        self.app.register_blueprint(_api_docs)


# 兼容0.0.1版本写法，后续版本中将移除
SimpleApi = CrudApi
