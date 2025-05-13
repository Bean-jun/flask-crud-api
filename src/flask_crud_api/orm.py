import http
import datetime
from flask import g, abort
from sqlalchemy.orm import Session
from sqlalchemy import select, Select
from sqlalchemy import func

from flask_crud_api.models import State


def get_session() -> Session:
    try:
        return g.session
    except RuntimeError:
        from api import session_factory

        return session_factory()


def get_valid_stmt(key, stmt: Select) -> Select:
    stmt = stmt.where(key == State.Valid)
    return stmt


def get_invalid_stmt(key, stmt: Select) -> Select:
    stmt = stmt.where(key == State.Invalid)
    return stmt


def get_delete_key(model_class):
    if isinstance(model_class, type):
        delete_key = model_class.state
    else:
        delete_key = model_class.class_.state
    return delete_key


class Orm:

    def get_queryset(self, *model_class) -> Select:
        stmt = select(*model_class)
        delete_key = get_delete_key(model_class[0])
        stmt = get_valid_stmt(delete_key, stmt)
        return stmt

    def get_queryset_count(self, *model_class) -> Select:
        stmt = select(func.count(model_class[0].pk))
        delete_key = get_delete_key(model_class[0])
        stmt = get_valid_stmt(delete_key, stmt)
        return stmt

    def execute_all(self, query: Select, scalers=True):
        with get_session() as session:
            if scalers:
                return session.execute(query).scalars().all()
            else:
                return session.execute(query).all()

    def execute_one_or_none(self, query: Select, none_raise=False, scalers=True):
        with get_session() as session:
            if scalers:
                queryset = session.execute(query).scalars().one_or_none()
            else:
                queryset = session.execute(query).one_or_none()
            if none_raise and not queryset:
                raise abort(http.HTTPStatus.NOT_FOUND)
            return queryset

    def execute_add_all(self, objs):
        with get_session() as session:
            session.add_all(objs)
            session.commit()

    def execute_add(self, obj):
        with get_session() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj

    def execute_delete(self, obj):
        with get_session() as session:
            setattr(obj, "state", State.Invalid)
            setattr(obj, "delete_time", datetime.datetime.now())
            session.add(obj)
            session.commit()

    def count(self, query: Select):
        with get_session() as session:
            return session.execute(query).scalar()
