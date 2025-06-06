# 定制化与扩展

`flask-crud-api` 在设计时考虑了可扩展性，允许开发者根据具体需求定制和扩展框架的默认行为。以下是一些主要的定制和扩展点：

## 1. `View` 的定制

在 `view.py` 中`CommonView` 和 `CommonDetailView` 是最核心的定制点。

### a. 覆盖标准方法

您可以覆盖 `CommonView`, `CommonDetailView`中的标准 HTTP 方法处理函数 (`get`, `post`, `put`, `delete`) 来实现自定义逻辑。

```python
from flask_crud_api.view import CommonView
from flask_crud_api.response import ok_response, bad_response
from .models import User

class UserView(CommonView):
    model = User

    def post(self, *args, **kwargs):
        # 在创建用户前进行额外验证
        data = dict(request.form)
        if not data.get('email') or '@' not in data['email']:
            return bad_response(data=None, msg="Invalid email format", code=400)
        
        # 调用父类方法完成创建
        # 注意：实际项目中，CommonView.post 直接创建，没有父类可调用的 post
        # 这里假设有一个可被重写的 _create_item 方法或直接操作 orm
        instance = self.from_serializer(self.model, data)
        # 假设有密码加密等逻辑
        # instance.set_password(data.get('password')) 
        instance = self.orm.execute_add(instance)
        return self.to_serializer(instance)

    def get(self, *args, **kwargs):
        # 自定义查询逻辑，例如只返回特定状态的用户
        stmt = self.get_queryset().where(User.status == 'active')
        stmt = self.query_filter(stmt) # 应用通用过滤器
        stmt = self.query_page_filter(stmt) # 应用分页
        result = self.orm.execute_all(stmt)
        return self.to_serializer(result, self.get_count()) # 注意 get_count 也可能需要调整
```

### b. 使用 `@action` 装饰器添加自定义路由

通过 `@action` 装饰器，您可以轻松地在 `CommonView` 中添加额外的非 CRUD 操作。

```python
from flask_crud_api.view import CommonView
from flask_crud_api.router import action
from flask_crud_api.response import ok_response
from .models import User

class UserView(CommonView):
    model = User

    @action(methods=["POST"], detail=True, url_path="set-password")
    def set_password(self, pk):
        user = self.get_object_instance(pk=pk) # 获取用户实例
        password = request.form.get('password')
        if not password:
            return bad_response(msg="Password is required.")
        # user.set_password(password) # 假设模型有此方法
        # self.orm.execute_add(user) # 保存更改
        return ok_response(msg="Password updated successfully.")
```

### c. 配置视图属性

视图中有许多可配置的属性来调整其行为：

-   `model`: 指定视图关联的 SQLAlchemy 模型。
-   `orm`: `Orm` 类的实例，用于数据库交互 (通常自动初始化)。
-   `serializer`: `Serializer` 类的实例，用于数据序列化 (通常自动初始化)。
-   `view_order_fields`: 配置允许排序的字段和方式 (详见“过滤与排序”文档)。
-   `view_filter_fields`: 配置允许过滤的字段和操作符 (详见“过滤与排序”文档)。
-   `view_join_model`, `view_join_model_key`, `view_join_filter_fields`: 配置连接查询的过滤 (详见“过滤与排序”文档)。
-   `view_page`: 指定分页过滤器类 (默认为 `PageFilter`)。
    -   `page_size`, `max_page_size`: 在视图级别配置分页参数。
-   `pk`: 用于详情视图的主键字段名 (默认为 `"pk"`)。
-   `decorators`: 应用于视图所有方法的装饰器列表。
-   `init_every_request`: 控制视图实例是否为每个请求重新创建。
-   `serializer_hooks`: 序列化过程中的钩子函数。

## 2. 自定义过滤器

您可以创建自己的过滤器类 (继承自 `BaseFilter` 或其他现有过滤器) 来实现复杂的查询逻辑。

```python
from flask_crud_api.filter import BaseFilter
from sqlalchemy import or_

class CustomSearchFilter(BaseFilter):
    def query_filter(self, stmt, view=None):
        search_term = request.args.get('custom_search')
        if search_term and hasattr(view.model, 'name') and hasattr(view.model, 'description'):
            # 假设在模型的 name 和 description 字段中搜索
            stmt = stmt.where(
                or_(
                    view.model.name.ilike(f"%{search_term}%"),
                    view.model.description.ilike(f"%{search_term}%")
                )
            )
        return stmt

# 在 CommonView 中使用自定义过滤器
class ProductView(CommonView):
    model = Product
    view_filters = (CustomSearchFilter, OrderFilter) # 替换或添加
```

## 3. 模型 (`models.py`) 的扩展

-   **自定义 `to_dict()`**: 在您的模型类中覆盖 `to_dict()` 方法，以精确控制序列化输出，例如处理关联对象、格式化特定字段或隐藏敏感信息。
-   **添加模型方法**: 为模型添加业务逻辑方法 (如 `user.set_password()`, `order.calculate_total()`)，这些方法可以在视图中被调用。
-   **SQLAlchemy 特性**: 利用 SQLAlchemy 的所有特性，如自定义数据类型、验证、事件监听器等。

## 4. `Orm` 类的扩展 (高级)

虽然不常需要，但您可以继承 `Orm` 类并覆盖其方法 (`get_queryset`, `execute_add`, `execute_delete` 等) 来改变核心的数据库交互逻辑。然后，您需要确保您的 `CommonView` 使用这个自定义的 `Orm` 类实例。

## 5. 响应格式与序列化

-   **自定义响应函数**: 如果标准的 `ok_response` 和 `bad_response` 不满足需求，您可以创建自己的响应构建函数。
-   **集成专业序列化库**: 对于复杂的序列化需求 (如输入验证、模式定义、嵌套结构)，可以考虑在 `CommonView` 的方法中或通过自定义 `Serializer` 类集成 Marshmallow 或 Pydantic 等库。
    ```python
    # 伪代码示例，在视图中使用 Pydantic
    # from pydantic import BaseModel
    # class ItemCreateSchema(BaseModel):
    #     name: str
    #     price: float

    # def post(self):
    #     try:
    #         validated_data = ItemCreateSchema(**request.form)
    #     except ValidationError as e:
    #         return bad_response(data=e.errors(), msg="Validation error", code=400)
        
    #     # ... 使用 validated_data.dict() 创建模型实例 ...
    ```

## 6. Flask 应用层面的扩展

由于 `flask-crud-api` 是一个 Flask 扩展，您可以利用所有 Flask 的特性来增强您的 API：

-   **Flask 配置**: 通过 `app.config` 进行各种配置。
-   **蓝图 (Blueprints)**: 组织大型应用。
-   **中间件 (Middleware)**: 添加请求处理钩子，如自定义认证、日志记录。
-   **错误处理**: 使用 `@app.errorhandler` 定制全局错误响应 (详见“错误处理”文档)。
-   **Flask 扩展**: 集成其他 Flask 扩展，如 Flask-Login (认证)、Flask-Caching (缓存)、Flask-Limiter (速率限制) 等。

## 7. OpenAPI/Swagger 文档定制

-   使用 `@swagger` 装饰器详细描述您的 API 端点 (详见“OpenAPI (Swagger) 集成”文档)。
-   如果需要更深层次的定制，可以考虑修改 `_openapi.py` 中的 `_SwaggerBuilder` 逻辑 (这属于高级用法，且可能在框架更新后需要调整)。

通过这些定制点，您可以将 `flask-crud-api` 从一个快速 CRUD 生成器转变为一个完全符合您特定业务需求的强大 API 框架。