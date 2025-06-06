# flask-crud-api

一个基于Flask的RESTful API框架，旨在帮助后端开发者快速构建高效且优雅的CRUD API。

## 功能特性

- 快速CRUD API开发
- 内置分页、过滤和排序功能
- Swagger/OpenAPI文档支持
- 简洁优雅的API设计

## 安装

1. 确保Python版本 ≥ 3.9
2. 安装依赖：
```bash
pip install flask-crud-api
```
3. 安装开发环境依赖（可选）：
```bash
pip install -e .[dev]
```

## 快速开始

1. 创建Flask应用并初始化API：
```python
from flask import Flask
from flask_crud_api.api import CrudApi

app = Flask(__name__)
app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"
app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True  # Enable Swagger documentation
CrudApi(app)
```

2. 定义模型并创建数据表：
```python
from sqlalchemy import Column, String, Float, DateTime
from flask_crud_api.models import BaseModel

class Book(BaseModel):
    __tablename__ = 'books'

    name = Column(String(255), comment="Book name")
    price = Column(Float(asdecimal=True), comment="Price")
```

3. 创建视图并注册路由：
```python
from flask import Blueprint
from flask_crud_api.router import Router
from flask_crud_api.view import CommonView
from flask_crud_api.decorators import swagger

# Create a blueprint and router
bp = Blueprint("v1", __name__, url_prefix="/api")
router = Router(bp)

@swagger(
    tags=["Books"],
    summary="Get a list of books",
    description="This endpoint retrieves a list of books.",
    auto_find_params=True,
    auto_find_body=True,
)
class BookView(CommonView):
    model = Book
    
    # 配置过滤字段
    view_filter_fields = (("name", "regexp"),)

# 注册视图路由
router.add_url_rule("/books", view_cls=BookView)

# 注册蓝图
app.register_blueprint(bp)
```

4. 运行应用：
```python
if __name__ == "__main__":
    app.run(debug=True, port=7256)
```

## API文档

启动服务后，访问 `http://127.0.0.1:7256/_docs` 路径可查看Swagger文档。

## 参数指南

1. 分页参数

```shell
__page         # 页码
__page_size    # 每页数据条数

# 使用此参数禁用分页（谨慎使用）
__page_disable
```

2. 数据创建和修改字段

```shell
# 字段模型和说明将在开发过程中提供
# 创建或修改数据时使用这些字段
```

3. 过滤字段

```shell
# 根据需求在后端代码中配置过滤字段

# 示例：
view_filter_fields = (("pk", "="),)  # 主键精确匹配
view_filters = (SearchFilter, )  # 使用搜索过滤器
```

4. 排序字段

```python
# 配置view_order_fields和view_filters实现排序功能

# 示例：
view_order_fields = (
    ("__order_pk", 'desc'),  # 按主键降序
    ("__order_pk", 'asc'),   # 按主键升序
)
view_filters = (SearchFilter, OrderFilter)  # 启用搜索和排序过滤器

# 使用 __order_pk=asc 按主键升序排序
# 使用 __order_pk=desc 按主键降序排序
```

## 参与贡献

1. Fork本项目
2. 创建特性分支
3. 提交Pull Request