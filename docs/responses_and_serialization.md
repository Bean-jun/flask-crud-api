# API 响应与序列化

`flask-crud-api` 框架定义了一套标准的 API 响应格式，并依赖于模型自身的序列化能力 (通常是 `to_dict()` 方法) 来准备要返回的数据。

## 1. 标准响应格式

所有的 API 响应都遵循统一的 JSON 结构，这有助于客户端以一致的方式处理来自不同端点的响应。该结构由 `response.py` 中的辅助函数生成。

```python
def _response(data, msg, code):
    return {
        "data": data,    # 实际的业务数据
        "msg": msg,      # 描述信息，例如 "ok", "error message"
        "code": code     # HTTP 状态码或业务状态码
    }
```

### 辅助函数

-   `ok_response(data, msg="ok")`: 用于生成成功的响应。默认情况下，`msg` 为 "ok"，`code` 为 `200`。
    ```python
    def ok_response(data, msg="ok"):
        return _response(data, msg, 200)
    ```

-   `bad_response(data, msg="bad")`: 用于生成错误的或不成功的响应。默认情况下，`msg` 为 "bad"，`code` 为 `400`。
    ```python
    def bad_response(data, msg="bad"):
        return _response(data, msg, 400)
    ```

### 示例响应

**成功响应 (例如获取单个产品):**

```json
{
    "data": {
        "id": 1,
        "name": "Laptop Pro",
        "price": 1200.00,
        "create_time": "2024-07-29T10:00:00Z",
        "update_time": "2024-07-29T10:00:00Z"
    },
    "msg": "ok",
    "code": 200
}
```

**错误响应 (例如验证失败):**

```json
{
    "data": null,  // 或者包含详细错误信息的对象
    "msg": "Invalid input: name is required",
    "code": 400
}
```

## 2. 数据序列化

框架本身不直接规定复杂的序列化方案 (如使用 Marshmallow 或 Pydantic 进行严格的模式定义和验证)，而是依赖于 SQLAlchemy 模型实例上的 `to_dict()` 方法将模型对象转换为字典，以便进行 JSON 序列化。

### `BaseModel.to_dict()`

在 `models.py` 中定义的 `BaseModel` (所有业务模型的基类) 通常会包含一个 `to_dict()` 方法。这个方法负责将模型的属性转换为一个字典。

```python
# (示意代码，具体实现可能在 BaseModel 或其子类中)
class BaseModel(db.Model):
    # ... 其他字段 ...

    def to_dict(self, exclude=None):
        """将模型实例转换为字典，可以排除某些字段"""
        data = {}
        exclude = exclude or []
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime.datetime):
                    data[column.name] = value.isoformat() # 日期时间格式化
                elif isinstance(value, decimal.Decimal):
                    data[column.name] = float(value) # Decimal 转 float
                else:
                    data[column.name] = value
        return data
```

### `CommonView` 中的使用

在 `CommonView` 的各个方法 (如 `get`, `post`, `put`, `delete`) 中，当需要返回模型数据时，会调用这个 `to_dict()` 方法。

-   对于单个对象的响应 (如 `GET /items/<id>`)，会直接调用 `item.to_dict()`。
-   对于列表对象的响应 (如 `GET /items`)，会对查询结果集中的每个对象调用 `item.to_dict()`，然后将这些字典组成的列表放入响应的 `data` 字段中。

### 序列化定制

-   **字段排除**: `to_dict(exclude=['password_hash', 'internal_field'])` 可以在调用时排除敏感或不需要的字段。
-   **关系加载**: 对于关联对象，`to_dict()` 的实现需要决定如何处理它们。可以选择：
    -   不包含关联对象。
    -   只包含关联对象的 ID。
    -   递归调用关联对象的 `to_dict()` 方法 (需要注意循环引用的问题)。
-   **数据格式化**: `to_dict()` 内部可以对特定类型的字段进行格式化，例如将 `datetime` 对象转换为 ISO 8601 字符串，将 `Decimal` 对象转换为浮点数或字符串。

虽然这种方式简单直接，但对于复杂的 API，开发者可能需要考虑引入更专业的序列化库来获得更强的数据验证、转换和文档生成能力。不过，对于快速原型开发和中小型项目，`to_dict()` 方法通常足够使用。