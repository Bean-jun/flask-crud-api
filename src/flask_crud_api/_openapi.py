import re

from flask import Flask
from werkzeug.routing.rules import Rule
from flask_crud_api.__version__ import version


default_exclude = {"/_docs/", "/static/"}
agrs_map = {
    "path": "string",
    "uuid": "string",
    "int": "integer",
    "float": "number",
}
templates = {
    "openapi": "3.0.1",
    "info": {"title": "flask crud api", "description": "", "version": version},
    # "tags": [{"name": "tag content"}],
    "paths": {},
    "components": {"schemas": {}, "securitySchemes": {}},
    "servers": [],
    "security": [],
}

_part_re = re.compile(
    r"""
    <
    (?:
        (?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)   # converter name
        (?:\((?P<arguments>.*?)\))?             # converter arguments
        :                                       # variable delimiter
    )?
    (?P<variable>[a-zA-Z_][a-zA-Z0-9_]*)      # variable name
    >
    """,
    re.VERBOSE,
)


def make_openapi_rule(rule: Rule):
    if ":" not in rule.rule or "<" not in rule.rule:
        return rule.rule, []

    valid_rule_list = []
    valid_rule_path = []
    for compile, _rule in zip(rule._parse_rule(rule.rule), rule.rule.split("/")):
        if compile.static:
            valid_rule_list.append(_rule)
            continue

        match = _part_re.match(_rule)
        if match is None:
            raise

        data = match.groupdict()
        if data["variable"] is not None:
            valid_rule_path.append(
                {
                    "name": data["variable"],
                    "type": agrs_map.get(data["converter"], "string"),
                }
            )
            valid_rule_list.append("{" + data["variable"] + "}")

    return "/".join(valid_rule_list), [
        {
            "name": argument["name"],
            "in": "path",
            "description": "",
            "required": True,
            "schema": {"type": argument["type"]},
        }
        for argument in valid_rule_path
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
