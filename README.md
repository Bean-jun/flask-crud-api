# flask-crud-api

本库旨在帮助后端开发人员快速构建一个基于`flask`框架的后端项目。

## 参数说明

1. 分页相关

```shell
__page 页码
__page_size 每页数量

# 如果需要禁用分页，可以使用此字段，请谨慎使用
__page_disable
```

2. 添加、修改数据字段

```shell
# 鉴于开发时，一次查询将会给出对应的字段模型及相关解释
# 创建、修改数据时可以使用此字段
```

3. 过滤字段

```shell
# 这部分字段请结合实际在后端代码中添加需要被过滤的字段内容

# 例如：
view_filter_fields = (("pk", "="),)
view_filters = (SearchFilter, )
```

4. 排序字段

```python
# 如果需要进行排序，请配置view_order_fields、view_filters
"""
view_order_fields = (("__order_pk", 'desc'), )
view_filters = (OrderFilter, ...)
"""

# 例如
view_order_fields = (
    ("__order_pk", 'desc'), 
    ("__order_pk", 'asc'), 
)
view_filters = (SearchFilter, OrderFilter)

# 传递query参数 __order_pk=asc 即可实现pk的升序
# 传递query参数 __order_pk=desc 即可实现pk的降序
```
