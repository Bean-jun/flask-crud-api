# OpenAPI (Swagger) 集成

`flask-crud-api` 内置了对 OpenAPI 规范的支持，可以自动生成 Swagger UI 界面，方便开发者浏览和测试 API 接口。

## 1. 启用 API 文档

要启用 API 文档功能，您需要在 Flask 应用的配置中设置 `FLASK_CRUD_API_OPEN_DOC_API` 为 `True`。

```python
from flask import Flask
from flask_crud_api import CrudApi # 或者 SimpleApi

app = Flask(__name__)

# 启用 API 文档
app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True

api = CrudApi(app)
# ... 定义您的模型和视图 ...
```

当此配置启用后，`CrudApi` 在初始化时 (`init_api_docs` 方法) 会注册一个名为 `_api_docs` 的 Blueprint。

## 2. 访问 API 文档

一旦启用，API 文档将通过以下端点提供：

-   **Swagger UI**: `/_docs/`
    访问此 URL 将展示 Swagger UI 界面，您可以在其中查看所有已注册的 API 端点、它们的参数、请求体、响应等，并可以直接在浏览器中进行接口测试。

-   **OpenAPI JSON**: `/_docs/openapi.json`
    此 URL 返回原始的 OpenAPI 3.0.1 规范的 JSON 文件。这个文件可以被其他 OpenAPI兼容的工具导入和使用。

### Blueprint 配置

`_api_docs` Blueprint 的详细配置如下：

-   **`static_folder`**: 指向包含 Swagger UI 静态资源 (CSS, JS, images) 的目录 (`flask_crud_api/static`)。
-   **`template_folder`**: 指向包含 Swagger UI 主 HTML 模板的目录 (`flask_crud_api/templates`)，主要是 `index.html`。
-   **`url_prefix`**: `/_docs`。

## 3. `@swagger` 装饰器

为了丰富自动生成的 OpenAPI 文档，框架提供了 `@swagger` 装饰器（实际上是 `Swagger` 类的别名，在 `decorator.py` 中定义）。您可以将此装饰器应用于您的 `CommonView` 子类或其方法，以提供更详细的元数据。

```python
from flask_crud_api.view import CommonView
from flask_crud_api import CrudApi
from flask_crud_api.decorator import swagger # 导入swagger别名
from .models import Product # 假设 Product 模型已定义

@swagger(
    tags=["Products"], 
    summary="Operations about products", 
    description="Provides CRUD operations for products."
)
class ProductView(CommonView):
    model = Product
    # ... 其他配置 ...

    @swagger(summary="Get a list of all products", description="Returns a paginated list of products.")
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    @swagger(
        summary="Create a new product",
        parameters=[
            # 这里可以定义更详细的请求体或参数描述，但目前框架的自动参数推断更常用
            # {"name": "name", "in": "formData", "required": True, "schema": {"type": "string"}},
            # {"name": "price", "in": "formData", "required": True, "schema": {"type": "number"}}
        ]
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
```

### `@swagger` 参数

-   `tags` (可选): 一个字符串或字符串列表，用于在 Swagger UI 中对 API 操作进行分组。
-   `summary` (可选): 一个简短的字符串，总结操作的目的。
-   `description` (可选): 一个更详细的字符串，描述操作。
-   `deprecated` (可选):布尔值，标记操作是否已弃用 (默认为 `False`)。
-   `parameters` (可选): 用于手动定义操作参数的列表。框架也会尝试根据视图的 `view_filter_fields` 和 `view_order_fields` 自动推断查询参数。路径参数会根据路由规则自动提取。
-   `login_required` (可选): 布尔值，指示此操作是否需要身份验证 (默认为 `False`)。如果为 `True`，会在 OpenAPI 文档中标记该操作需要安全凭证 (如 Bearer Token)。

### 装饰器行为

-   当 `@swagger` 应用于一个类时，其元数据会作为该类所有 HTTP 方法处理函数的默认值。
-   当 `@swagger` 应用于类中的特定方法 (如 `get`, `post`, 或通过 `@action` 定义的自定义方法) 时，它会覆盖或补充类级别的 Swagger 元数据。
-   `_openapi.py` 中的 `Swagger` 类及其 `__call__` 方法负责将这些元数据附加到视图类或方法上，以便 `_SwaggerBuilder` 在生成 `openapi.json` 时能够收集它们。
-   `_SwaggerBuilder` 会遍历应用中所有注册的路由规则，提取视图函数，并检查附加的 Swagger 元数据来构建 OpenAPI 路径 (paths) 和操作 (operations) 定义。

## 4. 自动参数推断

`_openapi.py` 中的 `Swagger` 类有一个 `_init_parameters` 方法，它会尝试根据 `CommonView` 上的 `view_filter_fields` (来自 `SearchFilter`) 和 `view_order_fields` (来自 `OrderFilter`) 自动为 `GET` 请求生成查询参数的文档。

-   路径参数 (如 `/items/{item_id}`) 会根据 Werkzeug 的路由规则自动识别并添加到 OpenAPI 文档中。

## 5. 局限性与未来改进 (TODOs in code)

代码中的注释表明了一些可以进一步完善的地方：

-   更精细的用户自定义参数 (`_init_user_parameters`)。
-   更完善的自动参数描述和示例值。
-   当类和方法都使用 `@swagger` 装饰器时，元数据的合并逻辑可以更细致。
-   请求体 (request body) 的自动文档生成 (例如，基于模型字段为 `POST` 和 `PUT` 请求生成)。
-   响应 (responses) 的自动文档生成，包括不同状态码的响应模式。

尽管如此，现有的 OpenAPI 集成已经为 `flask-crud-api` 提供了强大的 API 文档和测试能力。