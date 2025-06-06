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
app.config["FLASK_CRUD_API_DB_URL"] = "sqlite:///main.db"
app.config["FLASK_CRUD_API_OPEN_DOC_API"] = True  # Enable Swagger documentation
CrudApi(app)
```

2. Define models and create tables:
```python
from sqlalchemy import Column, String, Float, DateTime
from flask_crud_api.models import BaseModel

class Book(BaseModel):
    __tablename__ = 'books'

    name = Column(String(255), comment="Book name")
    price = Column(Float(asdecimal=True), comment="Price")
```

3. Create a view and register routes:
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
    
    # Configure filtering options
    view_filter_fields = (("name", "regexp"),)

# Register the view with the router
router.add_url_rule("/books", view_cls=BookView)

# Register the blueprint with the Flask app
app.register_blueprint(bp)
```

4. Run your application:
```python
if __name__ == "__main__":
    app.run(debug=True, port=7256)
```

## API Documentation

Access Swagger documentation at `http://127.0.0.1:7256/_docs` after starting the service.

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
