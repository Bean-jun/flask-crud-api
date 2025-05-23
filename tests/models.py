from sqlalchemy import Column, String, Text, Integer, DateTime, Float
from flask_crud_api.models import BaseModel, create_tables


class User(BaseModel):
    __tablename__ = "test_users"

    username = Column(String(255), nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")


class Book(BaseModel):
    __tablename__ = "test_books"

    uid = Column(Integer(), comment="用户ID")
    name = Column(String(255), comment="书名")
    publish = Column(DateTime, comment="发布时间")
    price = Column(Float(asdecimal=True), comment="价格")
