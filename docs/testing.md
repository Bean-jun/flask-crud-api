# 测试指南

为基于 `flask-crud-api` 构建的应用程序编写测试是确保其质量、可靠性和可维护性的关键步骤。由于 `flask-crud-api` 本质上是一个 Flask 扩展，因此测试方法与标准的 Flask 应用测试非常相似，通常会使用像 Pytest 这样的测试框架，并结合 Flask 的测试客户端。

## 1. 测试环境设置

### a. 测试配置

为测试环境创建一个单独的 Flask 配置通常是个好主意。这可以包括：

-   使用内存中的 SQLite 数据库或一个专门的测试数据库，以避免干扰开发或生产数据。
-   禁用某些在测试中不必要的特性 (例如，外部 API 调用模拟)。
-   设置 `TESTING = True`，这会改变 Flask 和某些扩展的行为 (例如，错误处理)。

```python
# config.py
class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ... other common configs ...

class TestingConfig(Config):
    TESTING = True
    FLASK_CRUD_API_DB_URL = "sqlite:///:memory:" # 使用内存数据库
    # 或者 "sqlite:///test.db" 并确保测试前/后清理
    FLASK_CRUD_API_OPEN_DOC_API = False # 通常测试时不需要API文档
    # ...其他测试特定配置...
```

### b. Pytest Fixtures

使用 Pytest 的 fixtures 来设置和拆卸测试环境非常方便。

-   **`app` fixture**: 创建并配置 Flask 应用实例。
-   **`client` fixture**: 提供 Flask 测试客户端，用于向应用发送 HTTP 请求。
-   **`db` fixture (或 `session` fixture)**: 初始化数据库，创建表，并在测试结束后清理数据。

```python
# tests/conftest.py
import pytest
from flask import Flask
from flask_crud_api import CrudApi
from flask_crud_api.models import Base # 假设您的模型基类
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 假设您的应用工厂模式
# from myapp import create_app 

@pytest.fixture(scope='session')
def app():
    # app = create_app(TestingConfig) # 如果使用应用工厂
    _app = Flask(__name__)
    _app.config["TESTING"] = True
    _app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///:memory:"
    _app.config["FLASK_CRUD_API_OPEN_DOC_API"] = False
    
    # 初始化 CrudApi 和数据库
    api = CrudApi()
    api.init_app(_app) # CrudApi.init_app 会处理数据库初始化
    
    # 如果 CrudApi.init_app 不完全处理表的创建，或者您有额外的模型
    # with _app.app_context():
    #     engine = api.app.extensions['sqlalchemy'].db.engine # 获取引擎的方式可能不同
    #     Base.metadata.create_all(bind=engine)

    yield _app

@pytest.fixture(scope='function') # function scope for db to reset per test
def db_session(app):
    # 获取由 CrudApi 初始化并配置的 session_factory
    # 这取决于 CrudApi 如何暴露 session_factory 或 engine
    # 假设 CrudApi 实例存储在 app.extensions['crud_api']
    # 或者直接从 flask_crud_api.api import session_factory (如果它是全局的且已初始化)
    from flask_crud_api.api import session_factory, engine # 需要确保它们已针对测试配置初始化
    
    Base.metadata.create_all(bind=engine) # 创建表
    session = session_factory()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine) # 清理表

@pytest.fixture()
def client(app):
    return app.test_client()
```

**注意**: 上述 `db_session` fixture 的实现依赖于如何从 `CrudApi` 实例或模块中获取已配置的 `session_factory` 和 `engine`。您可能需要根据 `flask-crud_api` 的实际实现调整这部分。

## 2. 编写测试用例

### a. 测试 CRUD 操作

针对每个 `View`，测试其核心的 CRUD (Create, Read, Update, Delete) 功能。

```python
# tests/test_product_api.py
import json
from myapp.models import Product # 假设您的 Product 模型

def test_create_product(client, db_session):
    response = client.post('/products/', data={'name': 'Test Product', 'price': '10.99'})
    assert response.status_code == 200 # 或 201 Created，取决于您的实现
    data = json.loads(response.data)
    assert data['code'] == 200
    assert data['data']['name'] == 'Test Product'
    
    # 验证数据库中是否已创建
    product_in_db = db_session.query(Product).filter_by(name='Test Product').first()
    assert product_in_db is not None
    assert product_in_db.price == 10.99

def test_get_product_list(client, db_session):
    # 先创建一些数据
    prod1 = Product(name='Product A', price=5.0)
    prod2 = Product(name='Product B', price=15.0)
    db_session.add_all([prod1, prod2])
    db_session.commit()

    response = client.get('/products/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['code'] == 200
    assert len(data['data']) == 2
    assert data['data'][0]['name'] == 'Product A'

def test_get_single_product(client, db_session):
    prod = Product(name='Detail Product', price=25.0)
    db_session.add(prod)
    db_session.commit()
    product_id = prod.pk # 假设主键是 pk

    response = client.get(f'/products/{product_id}/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['data']['name'] == 'Detail Product'

def test_update_product(client, db_session):
    prod = Product(name='Old Name', price=30.0)
    db_session.add(prod)
    db_session.commit()
    product_id = prod.pk

    response = client.put(f'/products/{product_id}/', data={'name': 'New Name', 'price': '35.0'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['data']['name'] == 'New Name'
    assert data['data']['price'] == 35.0

    updated_prod = db_session.query(Product).get(product_id)
    assert updated_prod.name == 'New Name'

def test_delete_product(client, db_session):
    prod = Product(name='To Delete', price=40.0)
    db_session.add(prod)
    db_session.commit()
    product_id = prod.pk

    response = client.delete(f'/products/{product_id}/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['msg'] == '删除成功' # 根据您的实现

    deleted_prod = db_session.query(Product).get(product_id)
    # 检查是否软删除或硬删除，根据您的模型设计
    # assert deleted_prod is None # 如果是硬删除
    # assert deleted_prod.status == 'deleted' # 如果是软删除
```

### b. 测试过滤和排序

验证 `view_filter_fields` 和 `view_order_fields` 是否按预期工作。

```python
def test_product_filtering(client, db_session):
    # ... 创建不同价格和名称的产品 ...
    response = client.get('/products/?price=>10&price=<=20')
    # ...断言返回了正确的产品...

def test_product_ordering(client, db_session):
    # ... 创建产品 ...
    response = client.get('/products/?__order_price=asc')
    # ...断言产品按价格升序排列...
```

### c. 测试分页

```python
def test_product_pagination(client, db_session):
    # ... 创建超过一页的产品 ...
    response = client.get('/products/?__page=2&__page_size=5')
    # ...断言返回了第二页的5个产品...
```

### d. 测试 `@action` 自定义路由

如果您的 `View` 有自定义的 `@action`，为它们编写专门的测试。

```python
# 假设 UserView 有一个 @action(url_path='promote', methods=['POST'])
def test_promote_user_action(client, db_session):
    # ... 创建一个用户 ...
    user_id = user.pk
    response = client.post(f'/users/{user_id}/promote/')
    assert response.status_code == 200
    # ... 断言用户状态已改变 ...
```

### e. 测试错误处理和边界情况

-   请求不存在的资源 (应返回 404)。
-   无效的输入数据 (应返回 400 或其他适当的错误码)。
-   未授权的访问 (如果实现了认证/授权，应返回 401 或 403)。
-   测试过滤器的边界条件。

## 3. 运行测试

通常使用 Pytest 命令行工具来运行测试：

```bash
pytest
```

或者指定特定文件或目录：

```bash
pytest tests/test_product_api.py
```

## 4. 覆盖率

使用像 `pytest-cov` 这样的工具来衡量测试覆盖率，以识别代码中未经测试的部分。

```bash
pip install pytest-cov
pytest --cov=myapp # 假设您的应用代码在 myapp 目录
```

全面的测试套件对于维护 `flask-crud-api` 应用的稳定性和促进安全的重构至关重要。