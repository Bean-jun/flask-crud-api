import re

from flask import Flask
from werkzeug.routing.rules import Rule
from flask_crud_api.__version__ import version
from flask_crud_api.decorator import Swagger


default_exclude = {"/_docs/", "/static/"}

agrs_map = {
    "path": "string",
    "uuid": "string",
    "int": "integer",
    "float": "number",
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


class _Swagger:

    def __init__(self, app: Flask):
        self.app = app
        self.templates = {
            "openapi": "3.0.1",
            "info": {"title": "flask crud api", "description": "", "version": version},
            # "tags": [{"name": "tag content"}],
            "paths": {},
            "components": {"schemas": {}, "securitySchemes": {}},
            "servers": [],
            "security": [],
        }
        self.swagger_key = Swagger.Key

    def builder(self, exclude=None):
        api_path = self._build_paths(exclude)
        self.templates["paths"] = api_path
        return self.templates

    def make_openapi_rule(self, rule: Rule):
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

    def _build_paths(self, exclude=None):
        api_path = {}
        for rule in self.app.url_map.iter_rules():
            view = self.app.view_functions[rule.endpoint]
            _rule, parameter = self.make_openapi_rule(rule)

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

            for method in view_methods:
                parameters = []
                if len(parameter):
                    parameters.extend(parameter)
                _method = method.lower()

                if not view_class:
                    swagger = view
                else:
                    if hasattr(view, "action"):
                        swagger = getattr(view, "action")
                    else:
                        swagger = getattr(view.view_class, _method)

                methods[_method] = self._build_path(swagger, parameters)

        return api_path

    def _build_path(self, swagger, parameters=None):
        if parameters is None:
            parameters = []

        res_summary = ""
        res_deprecated = False
        res_description = ""
        res_tags = []
        res_parameters = parameters
        res_responses = {}
        res_security = []

        if hasattr(swagger, self.swagger_key):
            _swagger = getattr(swagger, self.swagger_key)
            res_tags.extend([_swagger.tags])
            res_summary = _swagger.summary
            res_deprecated = _swagger.deprecated
            res_description = _swagger.description
            res_parameters.extend(_swagger.parameters)
        else:
            res_tags.extend([swagger.__name__])
            res_summary = swagger.__doc__
            res_description = swagger.__doc__

        return {
            "summary": res_summary,
            "deprecated": res_deprecated,
            "description": res_description,
            "tags": res_tags,
            "parameters": res_parameters,
            "responses": res_responses,
            "security": res_security,
        }


def render_api(app: Flask, exclude=None):
    if exclude is None:
        exclude = default_exclude

    swagger = _Swagger(app)
    return swagger.builder(exclude)
