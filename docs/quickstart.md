# 快速开始

本章节将引导您快速创建一个使用 `flask-crud-api` 的简单应用。

## 1. 创建 Flask 应用并初始化 API

首先，创建一个 Python 文件 (例如 `app.py`)，导入必要的模块并初始化 `CrudApi`：

```python
from flask import Flask
from flask_crud_api.api import CrudApi # 注意：在 README 中是 SimpleApi，这里统一为 CrudApi

# 创建 Flask 应用实例
app = Flask(__name__)

# 配置数据库连接 (这里使用 SQLite 作为示例)
app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"
# 开启接口文档支持
app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True

# 初始化 CrudApi
# 这会自动设置好 API 路由、数据库引擎等
CrudApi(app)

if __name__ == '__main__':
    app.run(debug=True)
```

**说明:**

-   `app = Flask(__name__)`: 创建一个标准的 Flask 应用实例。
-   `app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"`: 配置数据库连接字符串。`flask-crud-api` 使用 SQLAlchemy，因此您可以使用任何 SQLAlchemy 支持的数据库。
-   `app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True`: 开启接口文档支持。
-   `CrudApi(app)`: 这是框架的核心，它会将 CRUD 功能集成到您的 Flask 应用中。

## 2. 定义数据模型

接下来，定义您的数据模型。`flask-crud-api` 推荐使用其提供的 `BaseModel`，它包含了一些常用的字段 (如 `pk`, `create_time`, `update_time`, `is_delete`)。

在您的 `app.py` 或单独的 `models.py` 文件中定义模型：

```python
from sqlalchemy import Column, Integer, String
from flask_crud_api.models import BaseModel # 导入 BaseModel
from flask_crud_api.api import engine # 导入 SQLAlchemy 引擎

class User(BaseModel):
    __tablename__ = 'users'

    name = Column(String(50), nullable=False, comment="用户名")
    email = Column(String(100), unique=True, comment="邮箱")

# 创建所有定义的表 (如果它们尚不存在)
BaseModel.metadata.create_all(engine)
```

**说明:**

-   `User(BaseModel)`: 您的模型类继承自 `BaseModel`。
-   `__tablename__ = 'users'`: 定义数据库中的表名。
-   `Column(...)`: 使用 SQLAlchemy 的 `Column` 定义表字段。
-   `BaseModel.metadata.create_all(engine)`: 此行代码会根据您定义的模型在数据库中创建相应的表。通常在应用初始化时执行一次。

## 3. 创建视图 (View)

视图负责处理 HTTP 请求并与数据模型交互。对于 CRUD 操作，您可以创建一个继承自 `CommonView` 的类：

```python
from flask_crud_api.view import CommonView、CommonDetailView
# 假设 User 模型定义在 app.py 或已导入
# from .models import User # 如果 User 在 models.py

class UserView(CommonView):
    
    # 关联的模型类
    model = User
    # 可选配置，例如允许的查询字段、排序字段等
    # view_filter_fields = (("name", "like"), ("email", "="))
    # view_order_fields = (("__order_create_time", 'desc'),)


class UserDetailView(CommonDetailView):
    
    # 关联的模型类
    model = User

# 注册视图到 API
from flask_crud_api.router import Router
api_router = Router(app)
api_router.add_url_rule("/users", view_cls=UserView)
api_router.add_url_rule("/user/<int:pk>", view_cls=UserDetailView)
```

**说明:**

-   `UserView(CommonView)`: 您的视图类继承自 `CommonView`。
-   `model = User`: 将视图与 `User` 模型关联起来。
-   `flask-crud-api` 会自动为 `UserView` 生成标准的 CRUD 路由 (例如 `GET /users`, `POST /users`, `GET /users/<pk>`, `PUT /users/<pk>`, `DELETE /users/<pk>`)。

## 4. 运行应用

现在您可以运行您的 Flask 应用了：

```bash
python app.py
```

应用启动后，您可以通过 Postman 或浏览器访问以下端点：

-   `GET http://127.0.0.1:5000/users/`: 获取用户列表 (支持分页、过滤、排序)
-   `POST http://127.0.0.1:5000/users/`: 创建新用户 (请求体为 JSON)
-   `GET http://127.0.0.1:5000/users/<id>/`: 获取单个用户信息
-   `PUT http://127.0.0.1:5000/users/<id>/`: 更新用户信息 (请求体为 JSON)
-   `DELETE http://127.0.0.1:5000/users/<id>/`: 删除用户

## 5. 查看 API 文档

框架会自动生成 OpenAPI (Swagger) 文档。启动服务后，在浏览器中访问 `/_docs` (例如 `http://127.0.0.1:5000/_docs/`) 即可查看和交互式测试您的 API。

恭喜！您已经成功创建并运行了一个基本的 `flask-crud-api` 应用。