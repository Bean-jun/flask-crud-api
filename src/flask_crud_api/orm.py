import http
import datetime
import inspect
from flask import g, abort
from sqlalchemy import DateTime as SaDateTime
from sqlalchemy.engine import row
from sqlalchemy.orm import Session
from sqlalchemy import select, Select
from sqlalchemy import func

from flask_crud_api import utils
from flask_crud_api.models import State, orm_default_exclude
from flask_crud_api.response import ok_response


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


class Serializer:

    def __init__(self, view):
        self.view = view

    def from_serializer(self, model, serializer=None):
        if serializer is None:
            serializer = dict()

        if inspect.isclass(model):
            model = model()

        columns = model.metadata.tables.get(model.__tablename__).columns
        column_types = {column.key: column.type for column in columns}
        for key, value in serializer.items():
            if key in column_types:
                setattr(model, key, value)
                if isinstance(column_types[key], SaDateTime):
                    setattr(model, key, utils.str2datetime(value))
        return model

    def to_serializer(self, query, count=1, hooks=None, exclude=None):
        if hooks is None:
            hooks = self.view.serializer_hooks

        if not isinstance(hooks, (list, tuple)):
            hooks = [hooks]

        if not isinstance(query, (list, tuple)):
            query = [query]

        result = []
        for _query in query:
            if isinstance(_query, (row.Row)):
                _dict = self._instance_2_dict(_query, exclude)
                for _dict_ in _dict.keys():
                    _dict[_dict_] = self._instance_2_dict(_dict[_dict_], exclude)
            else:
                _dict = self._instance_2_dict(_query, exclude)

            for hook in hooks:
                _dict = hook(_dict, exclude)

            result.append(_dict)

        return ok_response(
            {
                "count": count,
                "result": result,
            }
        )

    def _instance_2_dict(self, query, exclude=None):
        if exclude is None:
            exclude = orm_default_exclude

        if hasattr(query, "to_dict"):
            return query.to_dict(exclude)
        if hasattr(query, "_asdict"):
            _dict = query._asdict()
            return {key: _dict[key] for key in _dict.keys() if key not in exclude}
        return query
