import inspect
import typing as t

from flask import current_app, views, request
from flask import abort
from flask_crud_api.orm import Orm, Serializer

from flask_crud_api.response import ok_response
from flask_crud_api.router import is_extra_action
from flask_crud_api.filter import PageFilter, SearchFilter, OrderFilter


class ViewRouterMixin:

    @classmethod
    def get_extra_actions(cls):
        return [
            (name, method) for name, method in inspect.getmembers(cls, is_extra_action)
        ]

    @classmethod
    def as_action_view(cls, action, *class_args: t.Any, **class_kwargs: t.Any):
        if cls.init_every_request:

            def view(**kwargs: t.Any):
                self = view.view_class(*class_args, **class_kwargs)
                self.action = action
                return current_app.ensure_sync(self.action.mapping)(self, **kwargs)

        else:
            self = cls(*class_args, **class_kwargs)
            self.action = action

            def view(**kwargs: t.Any):
                return current_app.ensure_sync(self.action.mapping)(self, **kwargs)

        if cls.decorators:
            view.__name__ = f"{cls.__name__}_{action.__name__}"
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)

        view.view_class = cls
        view.__name__ = f"{cls.__name__}_{action.__name__}"
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.methods = cls.methods
        view.provide_automatic_options = cls.provide_automatic_options
        return view


class ViewMixin:
    view_order_fields = (("__order_pk", 'asc'), )
    view_filters = (SearchFilter, OrderFilter)
    view_page = PageFilter
    serializer_hooks = ()

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model_class
        self.orm = Orm()
        self.serializer = Serializer(self)

    def from_serializer(self, model, serializer=None):
        return self.serializer.from_serializer(model, serializer)

    def to_serializer(self, query, count=1, hooks=None, exclude=None):
        return self.serializer.to_serializer(query, count, hooks, exclude)

    def query_filter(self, stmt):
        if not self.view_filters:
            return stmt

        for view_filter in self.view_filters:
            stmt = view_filter().query_filter(stmt, self)
        return stmt

    def query_page_filter(self, stmt):
        if not self.view_page:
            return stmt

        stmt = self.view_page().query_filter(stmt)
        return stmt

    def get_count(self):
        stmt = self.orm.get_queryset_count(self.model)
        stmt = self.query_filter(stmt)
        result = self.orm.execute_all(stmt)
        return result[-1]

    def get_queryset(self):
        stmt = self.orm.get_queryset(self.model)
        return stmt


class CommonView(ViewRouterMixin, ViewMixin, views.MethodView):

    def get(self, *args, **kwargs):
        stmt = self.get_queryset()
        stmt = self.query_filter(stmt)
        stmt = self.query_page_filter(stmt)
        result = self.orm.execute_all(stmt)
        return self.to_serializer(result, self.get_count())

    def post(self, *args, **kwargs):
        data = dict(request.form)
        instance = self.from_serializer(self.model, data)
        instance = self.orm.execute_add(instance)
        return self.to_serializer(instance)


class CommonDetailView(ViewRouterMixin, ViewMixin, views.MethodView):

    pk = "pk"

    def __init__(self, model_class, *args, **kwargs):
        super().__init__(model_class, *args, **kwargs)

    def get_pk(self, *args, **kwargs):
        if self.pk not in kwargs:
            return abort(404)
        return kwargs.get(self.pk)

    def query_object(self, *args, **kwargs):
        pk = self.get_pk(*args, **kwargs)
        stmt = self.get_queryset()
        stmt = stmt.where(getattr(self.model, self.pk) == pk)
        return stmt

    def get_object_instance(self, *args, **kwargs):
        stmt = self.query_object(*args, **kwargs)
        stmt = self.query_filter(stmt)
        result = self.orm.execute_one_or_none(stmt)
        if not result:
            return abort(404)
        return result

    def get(self, *args, **kwargs):
        result = self.get_object_instance(*args, **kwargs)
        return self.to_serializer(result)

    def post(self, *args, **kwargs):
        result = self.get_object_instance(*args, **kwargs)

        data = dict(request.form)
        instance = self.from_serializer(result, data)
        instance = self.orm.execute_add(instance)
        return self.to_serializer(instance)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def delete(self, *args, **kwargs):
        result = self.get_object_instance(*args, **kwargs)
        self.orm.execute_delete(result)
        return ok_response("删除成功")
