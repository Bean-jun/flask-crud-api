# 安装指南

## 环境要求

- Python 3.9 或更高版本

## 安装步骤

1.  **安装框架**

    您可以通过 pip 从 PyPI 安装 `flask-crud-api`：

    ```bash
    pip install flask-crud-api
    ```

2.  **开发环境安装 (可选)**

    如果您计划为该框架贡献代码或进行本地开发，可以从源码安装并包含开发依赖：

    ```bash
    # 克隆仓库 (如果您还没有)
    # git clone https://github.com/your-username/flask-crud-api.git
    # cd flask-crud-api

    pip install -e .[dev]
    ```

    这将会安装所有必要的依赖项，包括测试和代码风格检查工具。

## 验证安装

安装完成后，您可以在 Python 解释器中尝试导入框架来验证安装是否成功：

```python
import flask_crud_api
print(flask_crud_api.__version__)
```

如果输出了框架的版本号，则表示安装成功。