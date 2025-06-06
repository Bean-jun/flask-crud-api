# 请求过滤与排序

`flask-crud-api` 提供了强大的过滤和排序功能，允许客户端通过查询参数精确地控制 API 返回的数据。这些功能主要由 `filter.py` 中定义的过滤器类实现，并自动应用于继承自 `CommonView` 的视图的列表查询 (通常是 `GET` 请求)。

## 1. `BaseFilter`

所有过滤器都继承自 `BaseFilter`。它定义了一个 `query_filter(self, stmt: Select, view=None)` 方法，该方法接收一个 SQLAlchemy `Select` 查询对象和可选的视图实例，并返回修改后的查询对象。

## 2. `PageFilter`：分页

`PageFilter` 负责处理 API 响应的分页。

### 查询参数

-   `__page` (可选): 请求的页码，默认为 `1`。
-   `__page_size` (可选): 每页返回的项目数量，默认为视图中配置的 `page_size` (如果未配置，则为 `PageFilter.max_page`，默认是30)。请求的值会被限制在 `1` 和视图中配置的 `max_page_size` (或 `PageFilter.max_page`) 之间。
-   `__page_disable` (可选): 如果提供了此参数 (无论其值如何)，分页将被禁用，API 将返回所有符合条件的记录。请谨慎使用，以避免返回大量数据。

### `CommonView` 中的配置

您可以在 `CommonView` 子类中配置分页行为：

```python
class ProductView(CommonView):
    model = Product
```

### 示例请求

-   `GET /products?__page=2&__page_size=10`: 获取产品列表的第2页，每页10条。
-   `GET /products?__page_disable`: 获取所有产品，不进行分页。

## 3. `OrderFilter`：排序

`OrderFilter` 允许客户端根据一个或多个字段对返回结果进行排序。

### 查询参数

-   `__order_<field_name>=<direction>`: 指定排序字段和排序方向。
    -   `<field_name>`: 要排序的字段名 (模型中的属性名)。
    -   `<direction>`: 排序方向，可以是 `asc` (升序) 或 `desc` (降序)。

    例如: `__order_create_time=desc` 表示按创建时间降序排序。
    可以同时指定多个排序条件，例如 `GET /users?__order_name=asc&__order_create_time=desc`。

### `CommonView` 中的配置

您需要在 `CommonView` 子类中通过 `view_order_fields` 属性声明哪些字段允许用于排序以及它们对应的查询参数名和默认方向。

```python
class ProductView(CommonView):
    model = Product
    view_order_fields = (
        ("__order_name", 'asc'),       # 允许按名称升序排序，查询参数为 __order_name=asc
        ("__order_name", 'desc'),      # 允许按名称降序排序，查询参数为 __order_name=desc
        ("__order_price", 'asc'),      # 允许按价格升序排序，查询参数为 __order_price=asc
        ("__order_price", 'desc'),     # 允许按价格降序排序，查询参数为 __order_price=desc
        ("__order_create_time", 'desc') # 允许按创建时间降序排序，查询参数为 __order_create_time=desc
    )
```

-   元组的第一个元素是查询参数名 (必须以 `OrderFilter.order_field_prefix` 即 `__order_` 开头)。
-   元组的第二个元素是当客户端使用该查询参数时，实际应用的排序方向 (`asc` 或 `desc`)。
-   实际用于 SQLAlchemy `order_by` 的字段名是从查询参数名中去除前缀 `__order_` 得到的 (例如 `__order_name` -> `name`)。

### 示例请求

-   `GET /products?__order_price=asc`: 按价格升序获取产品列表。
-   `GET /products?__order_name=desc&__order_create_time=desc`: 先按名称降序，再按创建时间降序获取产品列表。

## 4. `SearchFilter`：字段搜索/过滤

`SearchFilter` 允许客户端根据模型字段的值进行过滤。

### 查询参数

查询参数的名称与您在 `view_filter_fields` 中配置的字段名一致。

### `CommonView` 中的配置

您需要在 `CommonView` 子类中通过 `view_filter_fields` 属性声明哪些字段允许用于过滤以及它们对应的 SQLAlchemy 操作符。

```python
class ProductView(CommonView):
    model = Product
    view_filter_fields = (
        ("name", "like"),        # name 字段进行模糊匹配 (ILIKE '%value%')
        ("category_id", "="),     # category_id 字段进行精确匹配
        ("price", ">"),          # price 字段大于指定值
        ("price", "<="),         # price 字段小于等于指定值
        ("status", "in"),        # status 字段值在提供的列表内 (例如 status=1,2)
        ("create_time", "between") # create_time 字段在指定的时间范围内 (例如 create_time=2023-01-01,2023-12-31)
    )
```

-   元组的第一个元素是查询参数名，也对应模型中的字段名。
-   元组的第二个元素是 SQLAlchemy 的比较操作符字符串，例如：
    -   `"="`: 等于 (`==`)
    -   `"!="`: 不等于
    -   `">"`: 大于
    -   `">="`: 大于等于
    -   `"<"`: 小于
    -   `"<="`: 小于等于
    -   `"like"`: 模糊匹配 (通常是 `ILIKE`，不区分大小写，包含 `%value%`)
    -   `"in"`: 值在列表中 (查询参数的值应为逗号分隔的字符串，例如 `status=1,2,3`)
    -   `"notin"`: 值不在列表中
    -   `"between"`: 值在两个值之间 (查询参数的值应为逗号分隔的两个值，例如 `create_time=2023-01-01 00:00:00,2023-01-31 23:59:59`)。
        -   对于 `SearchFilter.between_time_fields` (默认为 `{"create_time", "update_time", "entry_time"}`) 中定义的字段，`between` 操作符的值会自动通过 `utils.str2datetime` 转换为 `datetime` 对象。

### 示例请求

-   `GET /products?name=laptop`: 获取名称中包含 "laptop" 的产品。
-   `GET /products?category_id=5`: 获取类别 ID 为 5 的产品。
-   `GET /products?price=>1000&price=<=2000`: 获取价格大于1000且小于等于2000的产品。
-   `GET /products?create_time=between:2024-01-01 00:00:00,2024-01-31 23:59:59`: 获取创建时间在2024年1月的产品。

## 5. `SearchJoinFilter`：连接查询过滤

`SearchJoinFilter` 继承自 `SearchFilter`，并增加了对跨表连接 (JOIN) 查询的过滤支持。这允许您基于关联模型中的字段进行过滤。

### `CommonView` 中的配置

除了 `view_filter_fields` (用于主模型的过滤)，您还需要配置以下属性：

-   `view_join_model`: 一个元组或列表，包含要连接的 SQLAlchemy 模型类。
-   `view_join_model_key`: 一个元组或列表，包含连接条件。每个元素是一个二元组 `(join_model_field, main_model_field)`，表示 `join_model.field == main_model.field`。
-   `view_join_filter_fields`: 一个元组或列表，其结构与 `view_filter_fields` 类似，但用于定义关联模型的过滤字段。查询参数需要使用 `SearchJoinFilter.search_join_field_prefix` (默认为 `__join_`) 作为前缀，以区分主模型字段和关联模型字段。

```python
class BookView(CommonView):
    model = Book
    # 主模型过滤
    view_filter_fields = (("title", "like"),)

    # 连接查询配置
    view_join_model = (Author,)
    view_join_model_key = (("pk", "author_id"),) # Author.pk == Book.author_id
    view_join_filter_fields = (
        (("__join_name", "like"),), # 针对 Author 模型的 name 字段进行过滤
    )
```

### 查询参数

-   主模型的过滤参数与 `SearchFilter` 相同。
-   关联模型的过滤参数使用前缀 `__join_`，例如 `__join_name=John`。

### 示例请求

-   `GET /books?title=Python&__join_name=Doe`: 获取书名包含 "Python" 且作者名包含 "Doe" 的书籍。

### 内部机制

-   `make_join()`: 根据 `view_join_model` 和 `view_join_model_key` 构建 `OUTER JOIN` 语句，并确保只连接有效的关联记录 (通过 `get_valid_stmt` 检查关联模型的 `state`)。
-   `make_join_filter()`: 根据 `view_join_filter_fields` 为关联模型构建过滤条件。

这些过滤器共同为 `flask-crud-api` 提供了灵活而强大的数据查询能力。