from flask import Flask
from werkzeug.routing.rules import Rule
from flask_crud_api.__version__ import version


default_exclude = {"/_docs/", "/static/"}
templates = {
    "openapi": "3.0.1",
    "info": {"title": "flask crud api", "description": "", "version": version},
    # "tags": [{"name": "tag content"}],
    "paths": {},
    "components": {"schemas": {}, "securitySchemes": {}},
    "servers": [],
    "security": [],
}


def make_openapi_rule(rule: Rule):
    if ":" not in rule.rule:
        return rule.rule, []

    # TODO: 这里的逻辑需要好好处理一下, 先这样写，实现基本功能
    rule_list = rule.rule.split("/")
    valid_rule_list = []
    for _rule in rule_list:
        if not _rule.startswith("<"):
            valid_rule_list.append(_rule)
        else:
            for argument in rule.arguments:
                if argument in _rule:
                    valid_rule_list.append("{" + argument + "}")
    return "/".join(valid_rule_list), [
        {
            "name": argument,
            "in": "path",
            "description": "",
            "required": True,
            "schema": {"type": "integer"},
        }
        for argument in rule.arguments
    ]


def make_openapi_tags(view):
    if hasattr(view, "view_class"):
        return view.view_class.__doc__ or view.view_class.__name__
    return view.__name__


def render_api(app: Flask, exclude=None):
    if exclude is None:
        exclude = default_exclude

    api_path = {}
    for rule in app.url_map.iter_rules():
        view = app.view_functions[rule.endpoint]
        _rule, parameter = make_openapi_rule(rule)

        next_rule = False
        for _exclude in exclude:
            if _rule.startswith(_exclude):
                next_rule = True
                break

        if next_rule:
            continue

        api_path[_rule] = methods = {}

        view_methods = []
        view_class = False
        if hasattr(view, "view_class"):
            view_class = True
            view_methods = view.methods
        else:
            view_methods = rule.methods
        # view_methods = sorted(view_methods)

        for method in view_methods:
            parameters = []
            if len(parameter):
                parameters.extend(parameter)
            _method = method.lower()

            if not view_class:
                handler = view
            else:
                if hasattr(view, "action"):
                    hander_str = view.action.mapping[_method]
                    handler = getattr(view.view_class, hander_str)
                else:
                    handler = getattr(view.view_class, _method)

            methods[_method] = {
                "summary": handler.__doc__,
                "deprecated": False,
                "description": handler.__doc__,
                "tags": [make_openapi_tags(view)],
                "parameters": parameters,
                "responses": {},
                "security": [],
            }

    templates["paths"] = api_path
    return templates
