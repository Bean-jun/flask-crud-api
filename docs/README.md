# Flask CRUD API 文档

欢迎使用 Flask CRUD API (在代码库中也称为 `flask-crud-api`) 的文档！

`Flask CRUD API` 是一个旨在帮助开发者基于 Flask 快速构建 RESTful API 的库。它集成了 SQLAlchemy 用于数据库操作，并能自动生成 API 文档 (Swagger/OpenAPI)。

## 目录结构

本文档旨在提供全面的指南，帮助您理解、使用和扩展此框架。

-   **[简介 (Introduction)](introduction.md)**
    -   框架的设计目标和主要特性。
-   **[安装指南 (Installation)](installation.md)**
    -   环境要求和安装步骤。
-   **[快速开始 (Quickstart)](quickstart.md)**
    -   一个简单的示例，引导您完成第一个 API 的创建。
-   **[核心概念 (Core Concepts)](core_concepts.md)**
    -   深入理解框架的关键组件：`CrudApi` 应用实例、模型 (Model)、视图 (View)、路由 (Router)、过滤器 (Filter)、响应 (Response)。
-   **[视图与路由 (Views and Routing)](views_and_routing.md)**
    -   详细介绍 `CommonView`、`CommonDetailView`、`@action` 装饰器以及手动路由配置。
-   **[模型与 ORM (Models and ORM)](models_and_orm.md)**
    -   如何定义 SQLAlchemy 模型 (`BaseModel`)，以及 `Orm` 类提供的数据库操作方法。
-   **[请求过滤与排序 (Filtering and Sorting)](filtering_and_sorting.md)**
    -   使用内置过滤器 (`PageFilter`, `OrderFilter`, `SearchFilter`, `SearchJoinFilter`) 实现分页、排序和字段搜索。
-   **[API 响应与序列化 (Responses and Serialization)](responses_and_serialization.md)**
    -   标准的 API 响应格式以及如何通过模型的 `to_dict()` 方法进行数据序列化。
-   **[OpenAPI (Swagger) 集成](openapi_swagger.md)**
    -   如何启用和访问自动生成的 API 文档，以及如何使用 `@Swagger` 装饰器（也可通过 `from flask_crud_api.decorator import swagger` 导入的别名 `swagger`）丰富文档内容。
-   **[定制化与扩展 (Customization and Extension)](customization_and_extension.md)**
    -   指导如何覆盖默认行为、添加自定义逻辑、集成其他库等。
-   **[安全性考量 (Security)](security.md)**
    -   讨论 API 安全相关的最佳实践，包括认证、授权、输入验证等。
-   **[测试指南 (Testing)](testing.md)**
    -   如何为基于此框架构建的应用编写单元测试和集成测试。

我们希望这份文档能帮助您充分利用 `Flask CRUD API` 的强大功能！如果您有任何问题或建议，请通过项目的 GitHub 仓库提出。