import datetime

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class State:
    Valid = 1
    Invalid = 2

# orm 默认屏蔽字段
orm_default_exclude = {"delete_time", "state"}


class BaseModel(Base):
    __abstract__ = True

    pk = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    create_time = Column(DateTime, default=datetime.datetime.now, comment="创建时间")
    update_time = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        comment="更新时间",
    )
    delete_time = Column(DateTime, comment="删除时间")
    state = Column(Integer, default=State.Valid, comment="是否有效")

    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = orm_default_exclude

        result = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude
        }

        # for column in self.__table__.columns:
        #     if column.name in result:
        #         result[f"{column.name}-desc"] = column.comment

        return result


# 创建数据库表
def create_tables(engine):
    Base.metadata.create_all(engine)
