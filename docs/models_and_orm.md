# 数据模型与 ORM

`flask-crud-api` 使用 SQLAlchemy 作为其对象关系映射器 (ORM) 与数据库进行交互。本章节将介绍如何定义数据模型以及框架提供的 ORM 工具。

## 1. 定义数据模型

数据模型是 Python 类，它们定义了应用程序数据的结构以及如何映射到数据库表。

### `BaseModel`

框架提供了一个基础模型类 `flask_crud_api.models.BaseModel`，建议您的所有模型都继承自它。`BaseModel` 提供了以下常用字段：

-   `pk`: `Integer`, 主键, 自动递增。
-   `create_time`: `DateTime`, 创建时间, 默认为当前时间。
-   `update_time`: `DateTime`, 更新时间, 默认为当前时间，并在更新时自动更新。
-   `delete_time`: `DateTime`, 软删除时间, 默认为 `None`。
-   `state`: `Integer`, 数据状态, 默认为 `State.Valid` (值为1)。用于软删除，`State.Invalid` (值为2) 表示已删除。

```python
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from flask_crud_api.models import BaseModel, State

class Author(BaseModel):
    __tablename__ = 'authors'

    name = Column(String(100), nullable=False, comment="作者姓名")
    bio = Column(String(500), comment="作者简介")

    # 定义关系 (如果需要)
    books = relationship("Book", back_populates="author")

class Book(BaseModel):
    __tablename__ = 'books'

    title = Column(String(200), nullable=False, comment="书名")
    isbn = Column(String(20), unique=True, comment="ISBN")
    author_id = Column(Integer, ForeignKey('authors.pk'), comment="作者ID")

    author = relationship("Author", back_populates="books")
```

**主要特点:**

-   **`__tablename__`**: 定义数据库中的表名。
-   **`Column`**: 使用 SQLAlchemy 的 `Column` 定义表字段及其属性 (类型、是否可空、注释等)。
-   **`relationship`**: 使用 SQLAlchemy 的 `relationship` 定义模型之间的关系 (如一对多、多对多)。
-   **`to_dict(exclude=None)` 方法**: `BaseModel` 提供了一个 `to_dict` 方法，可以将模型实例转换为字典，方便序列化。默认会排除 `delete_time` 和 `state` 字段 (由 `orm_default_exclude` 定义)。

### `State` 枚举

`flask_crud_api.models.State` 是一个简单的类，定义了两种状态：

-   `State.Valid` (值为 1): 表示数据有效/未删除。
-   `State.Invalid` (值为 2): 表示数据无效/已软删除。

### 创建数据库表

您可以使用 `flask_crud_api.models.create_tables(engine)` 函数来根据定义的模型在数据库中创建所有表。通常在应用初始化时调用一次。

```python
from flask_crud_api.api import engine # 从 CrudApi 实例获取 engine
from flask_crud_api.models import create_tables

# ... 定义您的模型 ...

# 创建表
create_tables(engine)
```

## 2. ORM 工具 (`flask_crud_api.orm`)

`orm.py` 模块提供了一些辅助函数和类来简化与 SQLAlchemy 的交互。

### `get_session() -> Session`

获取当前的 SQLAlchemy `Session` 实例。它会尝试从 Flask 的应用上下文 `g.session` 中获取，如果失败则通过 `api.session_factory` 创建一个新的会话。

### `get_valid_stmt(key, stmt: Select) -> Select`

向给定的 SQLAlchemy `Select` 语句中添加条件，以仅查询 `state` 字段值为 `State.Valid` 的记录。

-   `key`: 通常是模型类的 `state` 属性 (例如 `User.state`)。
-   `stmt`: SQLAlchemy `Select` 查询对象。

### `get_invalid_stmt(key, stmt: Select) -> Select`

与 `get_valid_stmt` 类似，但查询 `state` 字段值为 `State.Invalid` 的记录。

### `get_delete_key(model_class)`

获取模型类用于软删除的状态字段 (通常是 `model.state`)。

### `Orm` 类

`Orm` 类封装了常见的数据库操作。

-   **`get_queryset(self, *model_class) -> Select`**: 创建一个基础的 `Select` 查询，默认会过滤掉软删除的记录 (即 `state == State.Valid`)。
    ```python
    orm_util = Orm()
    query = orm_util.get_queryset(User) # 获取查询所有有效用户的语句
    ```

-   **`get_queryset_count(self, *model_class) -> Select`**: 创建一个查询，用于统计有效记录的数量。
    ```python
    query = orm_util.get_queryset_count(User) # 获取统计有效用户数量的语句
    count = orm_util.count(query)
    ```

-   **`execute_all(self, query: Select, scalers=True)`**: 执行查询并返回所有结果。
    -   `scalers=True` (默认): 返回标量结果列表 (例如，模型实例列表)。
    -   `scalers=False`: 返回 `Row` 对象列表。

-   **`execute_one_or_none(self, query: Select, none_raise=False, scalers=True)`**: 执行查询并返回单个结果或 `None`。
    -   `none_raise=False` (默认): 如果未找到结果，返回 `None`。
    -   `none_raise=True`: 如果未找到结果，抛出 `HTTP 404 Not Found` 异常。

-   **`execute_add_all(self, objs)`**: 将多个对象批量添加到数据库会话并提交。

-   **`execute_add(self, obj)`**: 将单个对象添加到数据库会话，提交并刷新该对象 (以获取如自动生成的 ID 等信息)。返回已添加的对象。

-   **`execute_delete(self, obj)`**: 对指定的对象执行软删除操作。它会将对象的 `state` 设置为 `State.Invalid`，并记录 `delete_time`，然后提交更改。

-   **`count(self, query: Select)`**: 执行一个聚合查询 (通常是 `func.count()`) 并返回结果。

### `Serializer` 类

`Serializer` 类 (在 `orm.py` 中定义，但主要由 `View` 内部使用) 负责数据的序列化 (从模型实例到字典/JSON) 和反序列化 (从请求数据到模型实例)。

-   **`from_serializer(self, model, serializer=None)`**: 将字典数据反序列化 (填充) 到模型实例中。它会自动处理 SQLAlchemy `DateTime` 字段的字符串到 `datetime`对象的转换 (使用 `utils.str2datetime`)。
-   **`to_serializer(self, query, count=1, hooks=None, exclude=None)`**: 将查询结果 (单个模型实例或列表) 序列化为标准的 API 响应格式。它会使用模型上的 `to_dict()` 方法，并可以应用自定义的 `hooks` 函数进行数据转换。
    -   `query`: SQLAlchemy 查询结果 (模型实例或 `Row` 对象，或它们的列表)。
    -   `count`: (可选) 列表查询时的总数，用于分页。
    -   `hooks`: (可选) 一个或多个函数，用于在序列化后进一步处理字典数据。
    -   `exclude`: (可选) 序列化时要排除的字段列表。
-   **`_instance_2_dict(self, query, exclude=None)`**: 一个内部辅助方法，用于将单个模型实例或 `Row` 对象转换为字典，会优先调用实例的 `to_dict()` 或 `_asdict()` 方法。

这些 ORM 工具和 `BaseModel` 的设计旨在简化数据库操作，并为 `View` 提供强大的数据处理能力。