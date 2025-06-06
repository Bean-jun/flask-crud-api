# 视图与路由

在 `flask-crud-api` 中，视图 (Views) 负责处理进入的 HTTP 请求并返回响应。路由 (Routing) 决定了哪个视图函数应该处理特定的 URL 请求。

## 1. `CommonView`：基于模型的列表视图

`CommonView` 是框架提供的核心视图类，它为 SQLAlchemy 模型提供了完整的 CRUD (Create, Read, Update, Delete) 功能。通过继承 `CommonView` 并指定一个 SQLAlchemy 模型，您可以快速地为该模型创建一套 RESTful API 端点。

```python
from flask_crud_api.view import CommonView
from .models import User # 假设 User 模型已定义

class UserView(CommonView):
    model = User

    # 允许的过滤字段和操作符
    view_filter_fields = (
        ("name", "like"),      # 用户名模糊查询
        ("email", "="),        # 邮箱精确匹配
        ("create_time", "between") # 创建时间范围查询
    )

    # 允许的排序字段和默认排序方式
    view_order_fields = (
        ("__order_create_time", 'desc'), # 按创建时间降序
        ("__order_name", 'asc')         # 按名称升序
    )

    # 针对特定HTTP方法的装饰器 (例如，添加 Swagger 文档)
    # from flask_crud_api._openapi import Swagger
    # @Swagger(summary="Get a list of users", tags=["User Management"])
    # def get(self, *args, **kwargs):
    #     return super().get(*args, **kwargs)
```

### 自动生成的路由

对于上述 `UserView`，框架会自动生成以下路由 (假设模型名为 `user`，则路由前缀为 `/users/`):

-   `GET /users/`: 获取用户列表 (支持分页、过滤、排序)。
-   `POST /users/`: 创建一个新用户。

### `CommonView` 的主要可配置属性

-   `model`: (必须) 指定此视图关联的 SQLAlchemy 模型类。
-   `view_filter_fields`: 一个元组，定义了哪些模型字段可以用于过滤以及允许的过滤操作符。详见 [请求过滤与排序](filtering_and_sorting.md)。
-   `view_order_fields`: 一个元组，定义了哪些字段可以用于排序。详见 [请求过滤与排序](filtering_and_sorting.md)。
-   `view_join_model_key`, `view_join_filter_fields`, `view_join_model`: 用于配置跨表连接查询的过滤。详见 `SearchJoinFilter`。
-   `serializer_class`: (可选) 指定用于序列化/反序列化数据的 Marshmallow Schema 或 Pydantic Model。如果未提供，框架会尝试基于 SQLAlchemy 模型动态生成。
-   `query_hook`: (可选) 一个函数，允许在执行数据库查询之前修改 SQLAlchemy 查询对象 (Select 语句)。

### 覆盖 `CommonView` 方法

您可以覆盖 `CommonView` 中的标准 HTTP 方法 (如 `get`, `post`, `put`, `patch`, `delete`) 来实现自定义逻辑。在覆盖时，通常建议调用 `super()` 以保留基类的核心功能。

```python
class MyCustomUserView(CommonView):
    model = User

    def post(self, *args, **kwargs):
        # 在创建用户前执行一些自定义逻辑
        print("Before creating a user...")
        data = request.json
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data.pop('password'))
        
        # 调用父类的 post 方法完成创建
        response = super().post(*args, **kwargs)
        
        # 在创建用户后执行一些自定义逻辑
        print("After creating a user...")
        return response
```

## 2. `CommonDetailView`：基于模型的详细视图

`CommonDetailView` 同  `CommonView` 类似，但它专门用于处理单个资源的详细信息。例如，`GET /users/1/` 会获取 ID 为 1 的用户的详细信息。

```python
from flask_crud_api.view import CommonDetailView
from.models import User # 假设 User 模型已定义

class UserDetailView(CommonDetailView):
    model = User    # 关联的模型
    # ... 其他配置 ...
```

### 自动生成的路由

对于上述 `UserDetailView`，框架会自动生成以下路由 (假设模型名为 `user`，则路由前缀为 `/users/`):

-   `GET /users/<id>/`: 获取 ID 为 `<id>` 的用户的详细信息。
-   `PUT /users/<id>/`: 更新 ID 为 `<id>` 的用户的信息。
-   `PATCH /users/<id>/`: 部分更新 ID 为 `<id>` 的用户的信息。
-   `DELETE /users/<id>/`: 删除 ID 为 `<id>` 的用户。

### `CommonDetailView` 的主要可配置属性 

-   `model`: (必须) 指定此视图关联的 SQLAlchemy 模型类。
-   `serializer_class`: (可选) 指定用于序列化/反序列化数据的 Marshmallow Schema 或 Pydantic Model。如果未提供，框架会尝试基于 SQLAlchemy 模型动态生成。 
-   `query_hook`: (可选) 一个函数，允许在执行数据库查询之前修改 SQLAlchemy 查询对象 (Select 语句)。

### 覆盖 `CommonDetailView` 方法

您可以覆盖 `CommonDetailView` 中的标准 HTTP 方法 (如 `get`, `put`, `patch`, `delete`) 来实现自定义逻辑。在覆盖时，通常建议调用 `super()` 以保留基类的核心功能。

```python
class MyCustomUserDetailView(CommonDetailView):
    model = User

    def get(self, *args, **kwargs): # 覆盖 GET 方法
        # 在获取用户前执行一些自定义逻辑
        print("Before getting a user...")

        # 调用父类的 get 方法完成获取
        response = super().get(*args, **kwargs) 

        # 在获取用户后执行一些自定义逻辑
        print("After getting a user...")
        return response
```

## 3. `@action` 装饰器：添加自定义动作

除了标准的 CRUD 操作外，您可能需要为资源添加一些自定义的动作。可以使用 `@action` 装饰器在 `CommonView`、`CommonDetailView` 子类中定义额外的路由和处理方法。

```python
from flask_crud_api.router import action

class UserView(CommonDetailView):
    model = User

    @action(methods=['POST'], url_path='set_password')
    def set_password(self, pk):
        # pk 会自动从 URL 路径中获取，例如 /users/1/set_password/
        user = self.get_object_or_404(pk)
        password = request.json.get('password')
        if not password:
            return bad_response(msg="Password is required.")
        
        # 假设 User 模型有 set_password 方法
        user.set_password(password) 
        self.session.commit()
        return ok_response(msg="Password updated successfully.")

    @action(methods=['GET'], url_path='active_users_count')
    def active_users_count(self):
        count = self.session.query(self.model).filter_by(is_active=True).count()
        return ok_response(data={'active_users': count})
```

-   `@action(methods=['POST'], url_path='set_password')`:
    -   `methods`: 一个 HTTP 方法列表 (例如 `['GET']`, `['POST']`, `['GET', 'POST']`)。
    -   `url_path`: (可选) 自定义 URL 路径片段。如果未提供，将使用函数名。生成的 URL 将是 `/users/<id>/set_password/` (如果 `url_path` 包含 `<pk>` 或类似路径参数，则会匹配) 或 `/users/active_users_count/`。
-   装饰的方法会接收 `CommonDetailView` 实例作为 `self`。
-   如果 `url_path` 中定义了路径参数 (如 `<pk>`)，这些参数会传递给方法。

## 3. `Router` 类：手动注册路由

使用 `Router` 类，您可以手动注册视图函数到指定的 URL 路径。

## 4. 路由生成规则

-   `@action` 装饰的路由会附加到 `CommonView` `CommonDetailView` 的基础路由之后。
    -   如果 action 方法包含路径参数 (如 `pk`)，它通常会是 `/resource/<id>/action_path/`。
    -   如果不包含，它通常会是 `/resource/action_path/`。

理解视图的构建方式和路由的生成机制是使用 `flask-crud-api` 构建复杂应用的关键。