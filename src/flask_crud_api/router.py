import typing as t
import http
from flask import Flask, Blueprint, request, current_app, abort
from collections import UserDict


def is_extra_action(attr):
    return hasattr(attr, "mapping") and isinstance(attr.mapping, MethodMapper)


class MethodMapper(UserDict):

    def __init__(self, action, methods):
        super().__init__()
        self.action = action
        for method in methods:
            self[method] = self.action.__name__

    def __call__(self, view_instance, **kwds):
        self.view_instance = view_instance
        meth = getattr(self, request.method.lower(), None)

        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)

        assert meth is not None, f"Unimplemented method {request.method!r}"
        return current_app.ensure_sync(meth)(**kwds)

    def _meth(self, method):
        if method not in self:
            return abort(http.HTTPStatus.METHOD_NOT_ALLOWED)
        handler_str = self[method]
        if not hasattr(self.view_instance, handler_str):
            return abort(http.HTTPStatus.METHOD_NOT_ALLOWED)
        handler = getattr(self.view_instance, handler_str)
        return handler

    def get(self, *args, **kwargs):
        return self._meth("get")(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self._meth("post")(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self._meth("put")(*args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._meth("patch")(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._meth("delete")(*args, **kwargs)

    def head(self, *args, **kwargs):
        return self._meth("head")(*args, **kwargs)

    def options(self, *args, **kwargs):
        return self._meth("options")(*args, **kwargs)

    def trace(self, *args, **kwargs):
        return self._meth("trace")(*args, **kwargs)


def action(methods=None, url_path=None):
    methods = ["get"] if methods is None else methods
    methods = [method.lower() for method in methods]

    def decorator(func):
        func.mapping = MethodMapper(func, methods)
        func.url_path = url_path if url_path else func.__name__

        return func

    return decorator


class Router:

    def __init__(self, app: t.Union[Flask, Blueprint]):
        self._app = app

    def add_url_rule(
        self,
        rule: str,
        endpoint: t.Optional[str] = None,
        view_cls=None,
        provide_automatic_options: t.Optional[bool] = None,
        **options,
    ):
        self._app.add_url_rule(
            rule,
            endpoint,
            view_cls.as_view(view_cls.__name__),
            provide_automatic_options,
            **options,
        )
        # print(self.get_actions_routers(view_cls))
        actions = self.get_actions_routers(view_cls)
        for name, action in actions:
            url = f"{rule}/{action.url_path}"
            self._app.add_url_rule(
                url,
                endpoint,
                view_cls.as_action_view(action),
                provide_automatic_options,
                **options,
            )

    def get_actions_routers(self, view_cls):
        actions = view_cls.get_extra_actions()
        # print(actions)
        return actions
