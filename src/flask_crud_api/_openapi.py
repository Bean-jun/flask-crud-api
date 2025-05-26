import inspect
import itertools
import re

from flask import Flask
from flask.views import http_method_funcs
from werkzeug.routing.rules import Rule

from flask_crud_api.__version__ import version

default_exclude = {"/_docs/", "/static/"}

args_map = {
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


class Swagger:

    Key = "_swagger"

    def __init__(
        self,
        tags=None,
        summary="",
        deprecated=False,
        description="",
        parameters="",
        requestBody="",
        login_required=False,
    ):
        if tags is None:
            tags = []
        self.tags = tags if isinstance(tags, (tuple, list)) else [tags]
        self.summary = summary
        self.deprecated = deprecated
        self.description = description
        self.parameters = self._init_user_parameters(parameters)
        self.requestBody = self._init_user_requestBody(requestBody)
        self.login_required = login_required

    def _get_api_members(self, f):
        if not inspect.isclass(f):
            return

        from flask_crud_api.router import is_extra_action

        methods = []
        for m in http_method_funcs:
            if hasattr(f, m):
                methods.append(getattr(f, m))
        for _, m in inspect.getmembers(f, is_extra_action):
            methods.append(m)

        for m in methods:
            if not hasattr(m, self.Key):
                setattr(m, self.Key, self)
            else:
                # TODO: 做一个更新合并
                _m_member_swagger = getattr(m, self.Key)
                _m_member_swagger.tags.extend(self.tags)
                _m_member_swagger.parameters.extend(self.parameters)

    def _init_user_parameters(self, parameters=None):
        if parameters is None:
            return []
        # TODO: 完善用户传入参数初始化
        return []

    def _init_user_requestBody(self, requestBody=None):
        if requestBody is None:
            return []
        # TODO: 完善用户传入参数初始化
        return []

    def _init_parameters(self, f):
        if not inspect.isclass(f):
            return
        from flask_crud_api.filter import OrderFilter, SearchFilter

        search_list = SearchFilter().get_default_filter(f)
        order_list = OrderFilter().get_default_order(f)

        parameters = []
        # TODO: 需要完善
        for param, _action in itertools.chain(search_list, order_list):
            parameters.append(
                {
                    "name": param,
                    "in": "query",
                    "description": param,  # TODO: 描述
                    "required": False,
                    "example": _action,  # TODO: 例子
                    "schema": {"type": "string"},  # TODO: 类型
                }
            )
        self.parameters.extend(parameters)

    def _init_requestBody(self, f):
        if not inspect.isclass(f):
            return
        if not getattr(f, "model"):
            return

        properties = {}
        for column in f.model.__table__.columns:
            properties[column.name] = {
                "description": column.comment,
                # "example": "",  # TODO: 例子
                "type": "string",  # TODO: 类型
            }
        self.requestBody = properties

    def __call__(self, f):
        # TODO: 若用户没有设置初始值，需要完善一下
        self._init_parameters(f)
        self._init_requestBody(f)

        # 默认用户所有的接口都使用这个装饰器
        setattr(f, self.Key, self)

        # 为当前类所有方法赋值类的swagger信息
        self._get_api_members(f)
        return f


class _SwaggerBuilder:

    def __init__(self, app: Flask):
        self.app = app
        self.templates = {
            "openapi": "3.0.1",
            "info": {"title": "flask crud api", "description": "", "version": version},
            # "tags": [{"name": "tag content"}],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "authorization": {"type": "http", "scheme": "bearer"}
                },
            },
            "servers": [],
            "security": [],
        }
        self.templates_security_private = [{"authorization": []}]
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
                        "type": args_map.get(data["converter"], "string"),
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

                    if not hasattr(swagger, self.swagger_key):
                        swagger = view.view_class

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
        res_body = {}
        res_responses = {}
        res_security = []

        if hasattr(swagger, self.swagger_key):
            _swagger = getattr(swagger, self.swagger_key)
            res_tags.extend(_swagger.tags)
            res_summary = _swagger.summary
            res_deprecated = _swagger.deprecated
            res_description = _swagger.description
            res_parameters.extend(_swagger.parameters)
            res_body = _swagger.requestBody
            res_security = (
                self.templates_security_private if _swagger.login_required else []
            )
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
            "requestBody": {
                "content": {
                    "multipart/form-data": {
                        "schema": {"type": "object", "properties": res_body}
                    }
                }
            },
            "responses": res_responses,
            "security": res_security,
        }


def render_api(app: Flask, exclude=None):
    if exclude is None:
        exclude = default_exclude

    swagger = _SwaggerBuilder(app)
    return swagger.builder(exclude)
