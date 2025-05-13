from flask import Flask
from flask_crud_api.api import SimpleApi
import settings


def init_api(app: Flask):
    from api.urls import init_app

    init_app(app)

    if settings.dev:
        for url in app.url_map.iter_rules():
            print(url)


def create_app():
    app = Flask(__name__)
    app.config["DB_URL"] = "sqlite:///main.db"
    SimpleApi(app)

    from models import create_tables
    from flask_crud_api.api import engine
    create_tables(engine)

    init_api(app)

    # if settings.dev:
    #     from werkzeug.middleware.profiler import ProfilerMiddleware

    #     # 需要进行数据库迁移时，注释此行
    #     app = ProfilerMiddleware(app, stream=None, profile_dir=".profiler")
    return app


if __name__ == "__main__":
    from werkzeug.serving import run_simple

    app = create_app()

    run_simple(settings.hostname, settings.hostport, app)
