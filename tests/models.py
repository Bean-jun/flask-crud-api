from sqlalchemy import Column, String, Text, Integer
from flask_crud_api.models import BaseModel, create_tables


class UserModel(BaseModel):
    __tablename__ = "user_models"

    username = Column(String(255), nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")


class HTTPModel(BaseModel):
    __tablename__ = "http_models"

    uid = Column(Integer(), comment="用户ID")
    path = Column(String(255), comment="请求路径")
    method = Column(String(255), comment="请求方法")
    args = Column(String(255), comment="查询参数")
    form = Column(Text, comment="请求体参数")
