from sqlalchemy import Column, String, Text
from flask_crud_api.models import BaseModel, create_tables



class HTTPModel(BaseModel):
    __tablename__ = 'http_models'

    path = Column(String(255), comment="请求路径")
    method = Column(String(255), comment="请求方法")
    args = Column(String(255), comment="查询参数")
    form = Column(Text, comment="请求体参数")
