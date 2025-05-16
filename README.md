# flask-crud-api

<a style='text-align=center'>[中文文档](./README_ZH.md)</a>

A Flask-based RESTful API framework designed to help backend developers quickly build efficient and elegant CRUD APIs.

## Features

- Rapid CRUD API Development
- Built-in Pagination, Filtering, and Sorting
- Swagger/OpenAPI Documentation Support
- Clean and Elegant API Design

## Installation

1. Ensure Python version ≥ 3.9
2. Install dependencies:
```bash
pip install flask-crud-api
```
3. Additional dependencies for development:
```bash
pip install -e .[dev]
```

## Quick Start

1. Create a Flask application and initialize the API:
```python
from flask import Flask
from flask_crud_api.api import CrudApi

app = Flask(__name__)
app.config["DB_URL"] = "sqlite:///main.db"
CrudApi(app)
```

2. Define models and create tables:
```python
from sqlalchemy import Column, Integer, String
from flask_crud_api.models import BaseModel

class User(BaseModel):
    __tablename__ = 'users'

    name = Column(String(50))
```

## API Documentation

Access Swagger documentation at `/_docs` after starting the service.

## Parameter Guide

1. Pagination Parameters

```shell
__page         # Page number
__page_size    # Items per page

# Use this parameter to disable pagination (use with caution)
__page_disable
```

2. Data Creation and Modification Fields

```shell
# Field models and explanations will be provided during development
# Use these fields when creating or modifying data
```

3. Filter Fields

```shell
# Configure filter fields in backend code based on requirements

# Example:
view_filter_fields = (("pk", "="),)
view_filters = (SearchFilter, )
```

4. Sorting Fields

```python
# Configure view_order_fields and view_filters for sorting
"""
view_order_fields = (("__order_pk", 'desc'), )
view_filters = (OrderFilter, ...)
"""

# Example:
view_order_fields = (
    ("__order_pk", 'desc'), 
    ("__order_pk", 'asc'), 
)
view_filters = (SearchFilter, OrderFilter)

# Use __order_pk=asc for ascending order by primary key
# Use __order_pk=desc for descending order by primary key
```

## Contributing

1. Fork the project
2. Create a feature branch
3. Submit a Pull Request
