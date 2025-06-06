# 核心概念

理解 `flask-crud-api` 的核心概念将帮助您更有效地使用和扩展该框架。

## 1. `CrudApi` 应用实例

`CrudApi` 类是框架的入口点。当您实例化 `CrudApi(app)` 时，它会执行以下操作：

-   **初始化 SQLAlchemy**: 设置数据库引擎 (`engine`) 和会话 (`SessionLocal`)，基于您在 Flask 应用配置中提供的 `FLASK_CRUD_API_DB_URL`。
-   **集成 OpenAPI (Swagger)**: 设置路由 `/openapi.json` 以提供 OpenAPI 规范，并设置 `/_docs` 路由以展示 Swagger UI 界面。
-   **自动注册视图 (ModelView)**: 扫描项目中所有继承自 `ModelView` 的类，并为它们自动生成 CRUD 路由。
-   **提供基础模型 (`BaseModel`)**: 包含常用的数据库字段，如 `pk`, `create_time`, `update_time`, `is_delete`。

## 2. 模型 (`Model`)

数据模型使用 SQLAlchemy 定义。框架推荐您的模型继承自 `flask_crud_api.models.BaseModel`，这样可以自动获得一些基础字段和功能。

```python
from sqlalchemy import Column, String
from flask_crud_api.models import BaseModel

class Product(BaseModel):
    __tablename__ = 'products'
    name = Column(String(100), nullable=False)
    description = Column(String(255))
```

-   模型定义了数据的结构和与数据库表的映射。
-   `BaseModel` 提供了主键 `id`，创建时间 `create_time`，更新时间 `update_time` 和软删除标记 `is_delete`。

## 3. 视图 (`View`)

视图是处理 HTTP 请求的核心组件。`flask-crud-api` 提供了 `CommonView`，它封装了针对单个模型的标准 CRUD 操作逻辑。

```python
from flask_crud_api.view import CommonView
from .models import Product # 假设 Product 模型已定义

class ProductView(CommonView):

    view_filter_fields = (("name", "like"), ("description", "like")) # 允许的过滤字段
    view_order_fields = (("__order_create_time", 'desc'), ("__order_name", 'asc')) # 允许的排序字段
    model = Product # 关联的模型类
```

-   通过将 `model` 属性设置为您的 SQLAlchemy 模型类，`CommonView` 会自动处理该模型的增删改查操作。
-   您可以覆盖 `CommonView` 中的方法或配置其属性来自定义行为，例如分页大小、允许的过滤字段、排序字段等。
-   框架会自动为每个 `CommonView` 生成一组 RESTful API 端点。

## 4. 路由 (`Router`)

路由负责将 URL 路径映射到相应的视图处理函数。

-   **自动路由**: 对于继承自 `CommonView` 的视图，框架会自动生成标准的 CRUD 路由。例如，对于 `ProductView`，会生成 `/products/`路由。
-   **自定义路由**: 您仍然可以使用 Flask 的标准方式 (`@app.route` 或 `app.add_url_rule`) 添加自定义路由。对于更复杂的视图逻辑或非 CRUD 操作，这是必要的。
-   **Action 路由**: 支持通过 `@action` 装饰器添加额外的路由到视图中，这些路由通常用于执行特定于资源的操作，而不是标准的 CRUD。

## 5. 过滤器 (`Filter`)

过滤器允许客户端通过查询参数来筛选和排序 API 返回的数据。

-   **`PageFilter`**: 处理分页逻辑，通过 `__page` 和 `__page_size` 参数控制返回的数据页码和每页数量。
-   **`OrderFilter`**: 处理排序逻辑，通过 `__order_<field_name>` 参数控制排序字段和顺序 (asc/desc)。需要在视图中配置 `view_order_fields`。
-   **`SearchFilter`**: 处理字段过滤逻辑，允许根据模型字段进行精确匹配、模糊查询、范围查询等。需要在视图中配置 `view_filter_fields`。
-   **`SearchJoinFilter`**: 支持跨表连接查询的过滤。

这些过滤器会自动应用于继承自 `CommonView` 的视图的 `GET` 列表请求。

## 6. 响应 (`Response`)

框架提供了标准的 JSON 响应格式：

```json
{
  "code": 200, // HTTP 状态码或业务状态码
  "msg": "ok",   // 描述信息
  "data": { ... } // 实际数据或列表
}
```

-   `ok_response(data, msg)`: 用于成功的响应。
-   `bad_response(data, msg)`: 用于客户端错误或业务逻辑错误的响应。

## 7. OpenAPI (Swagger) 集成

`flask-crud-api` 自动为所有通过 `CommonView` 或 `@Swagger` 装饰器修饰的路由生成 OpenAPI 3.0 规范。

-   规范文件位于 `/openapi.json`。
-   交互式 Swagger UI 界面位于 `/_docs`。
-   您可以使用 `@Swagger()` 装饰器为自定义视图或 `CommonView` 中的方法提供更详细的 API 文档信息 (如标签、摘要、参数描述等)。

理解这些核心概念将帮助您更好地利用 `flask-crud-api` 的功能，并根据您的需求进行定制和扩展。