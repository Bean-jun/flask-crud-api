import typing as t
import inspect
import itertools
import dataclasses
from flask.views import http_method_funcs

requestBodyType = t.Optional[t.Union["BodyParam", t.List["BodyParam"]]]
parametersType = t.Optional[t.Union["QueryParam", t.List["QueryParam"]]]


@dataclasses.dataclass()
class QueryParam:

    name: str
    description: t.Optional[str] = ""
    required: bool = False
    example: t.Optional[str] = ""
    _in: str = "query"
    _type: str = "string"

    @staticmethod
    def dict_factory(result):
        _result = []
        for field, value in result:
            if field == "_in":
                _result.append(("in", value))
            elif field == "_type":
                _result.append(("schema", {"type": value}))
            else:
                _result.append((field, value))

        return dict(_result)


@dataclasses.dataclass()
class BodyParam:

    name: str
    description: t.Optional[str] = ""
    example: t.Optional[str] = ""
    _type: str = "string"

    @staticmethod
    def dict_factory(result):
        _result = []
        for field, value in result:
            if field == "_type":
                _result.append(("type", value))
            else:
                _result.append((field, value))

        return dict(_result)


class Swagger:

    Key = "_swagger"

    def __init__(
        self,
        tags: t.Optional[t.List[str]] = None,
        summary: str = "",
        description: str = "",
        deprecated: bool = False,
        parameters: parametersType = None,
        requestBody: requestBodyType = None,
        login_required: bool = False,
        auto_find_params: bool = False,
        auto_find_body: bool = False,
    ):
        """Swagger文档

        Args:
            tags (t.Optional[t.List[str]], optional): 接口tags. Defaults to None.
            summary (str, optional): 接口描述. Defaults to "".
            description (str, optional): 接口详细内容. Defaults to "".
            deprecated (bool, optional): 接口是否弃用. Defaults to False.
            parameters (parametersType, optional): 接口查询参数. Defaults to None.
            requestBody (requestBodyType, optional): 接口请求体参数. Defaults to None.
            login_required (bool, optional): 是否要求登录(仅仅供swagger验证使用). Defaults to False.
            auto_find_params (bool, optional): 是否自动获取接口查询参数. Defaults to False.
            auto_find_body (bool, optional): 是否自动获取接口请求体参数. Defaults to False.
        """
        if tags is None:
            tags = []
        self.tags = tags if isinstance(tags, (tuple, list)) else [tags]
        self.summary = summary
        self.deprecated = deprecated
        self.description = description
        self.parameters = self._init_user_parameters(parameters)
        self.requestBody = self._init_user_requestBody(requestBody)
        self.login_required = login_required
        self.auto_find_params = auto_find_params
        self.auto_find_body = auto_find_body

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
                if not _m_member_swagger.parameters:
                    _m_member_swagger.parameters.extend(self.parameters)
                if not _m_member_swagger.requestBody:
                    _m_member_swagger.requestBody.update(self.requestBody)

    def _init_user_parameters(self, parameters: parametersType = None):
        if parameters is None:
            return []

        if not isinstance(parameters, (list, tuple)):
            parameters = [parameters]

        _parameters = []
        for parameter in parameters:
            _parameters.append(
                dataclasses.asdict(parameter, dict_factory=QueryParam.dict_factory)
            )
        return _parameters

    def _init_user_requestBody(
        self,
        requestBody: requestBodyType = None,
    ):
        if requestBody is None:
            return {}

        if not isinstance(requestBody, (list, tuple)):
            requestBody = [requestBody]

        properties = {}
        for body in requestBody:
            properties[body.name] = dataclasses.asdict(
                body, dict_factory=BodyParam.dict_factory
            )
        return properties

    def _init_parameters(self, f):
        if not inspect.isclass(f):
            return
        from flask_crud_api.filter import OrderFilter, SearchFilter

        search_list = SearchFilter().get_default_filter(f)
        order_list = OrderFilter().get_default_order(f)

        parameters = []
        for param, _action in itertools.chain(search_list, order_list):
            parameters.append(
                dataclasses.asdict(
                    QueryParam(
                        name=param,
                        description=param,
                        required=False,
                        example=_action,
                        _in="query",
                        _type="string",
                    ),
                    dict_factory=QueryParam.dict_factory,
                )
            )
        self.parameters.extend(parameters)

    def _init_requestBody(self, f):
        if not inspect.isclass(f):
            return
        if not getattr(f, "model"):
            return

        properties = {}
        for column in f.model.__table__.columns:

            properties[column.name] = dataclasses.asdict(
                BodyParam(
                    name=column.name,
                    description=column.comment,
                    example="",
                    _type="string",
                ),
                dict_factory=BodyParam.dict_factory,
            )
        properties.update(self.requestBody)
        self.requestBody = properties

    def __call__(self, f):
        # TODO: 若用户没有设置初始值，需要完善一下
        if self.auto_find_params:
            self._init_parameters(f)
        if self.auto_find_body:
            self._init_requestBody(f)

        # 默认用户所有的接口都使用这个装饰器
        setattr(f, self.Key, self)

        # 为当前类所有方法赋值类的swagger信息
        self._get_api_members(f)
        return f
