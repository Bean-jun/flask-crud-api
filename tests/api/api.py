from flask import request
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from flask_crud_api.filter import SearchJoinFilter
from flask_crud_api.orm import get_delete_key, get_valid_stmt
from flask_crud_api.view import CommonView, CommonDetailView
from flask_crud_api.router import action

from models import HTTPModel, UserModel
from .hooks import hook_http_model_user, hook_http_model_user_no_N_ADD_ONE


class UserModelView(CommonView):
    """用户"""
    def __init__(self):
        super().__init__(UserModel)

    def post(self, *args, **kwargs):
        data = dict(request.form)
        instance: UserModel = self.from_serializer(self.model, data)
        instance.password = generate_password_hash(instance.password)
        instance = self.orm.execute_add(instance)
        return self.to_serializer(instance)


class UserModelDetailView(CommonDetailView):
    """用户明细"""
    def __init__(self):
        super().__init__(UserModel)


class HTTPModelView(CommonView):
    view_filter_fields = (
        ("method", "="),
        ("path", "regexp"),
    )
    view_join_model_key = (("pk", "uid"),)
    view_join_model = (UserModel,)
    view_filters = (SearchJoinFilter,)
    serializer_hooks = (hook_http_model_user,)

    def __init__(self):
        super().__init__(HTTPModel)
    
    def get(self, *args, **kwargs):
        """获取HTTP记录"""
        return super().get(*args, **kwargs)

    @action()
    def get_userinfo_no_N_ADD_ONE(self):
        """尝试解决N+1查询问题"""
        stmt = self.orm.get_queryset(self.model, UserModel)
        stmt = self.query_filter(stmt)
        stmt = self.query_page_filter(stmt)
        result = self.orm.execute_all(stmt, False)
        return self.to_serializer(
            result,
            self.get_count(),
            hook_http_model_user_no_N_ADD_ONE,
            {
                "password",
            },
        )

    @action()
    def get_patch(self):
        """获取部分数据内容"""
        stmt = select(
            self.model.path.label("path"),
            self.model.method.label("method"),
            UserModel.pk.label("uid"),
        )
        delete_key = get_delete_key(self.model)
        stmt = get_valid_stmt(delete_key, stmt)
        stmt = self.query_filter(stmt)
        stmt = self.query_page_filter(stmt)
        result = self.orm.execute_all(stmt, False)
        return self.to_serializer(
            result,
            self.get_count(),
            hook_http_model_user_no_N_ADD_ONE,
            {
                "password",
                "uid",
            },
        )


class HTTPModelDetailView(CommonDetailView):
    def __init__(self):
        super().__init__(HTTPModel)
