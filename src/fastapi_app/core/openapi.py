"""OpenAPI / Swagger 文档元数据：分组标签与接口说明。"""

# 导入 FastAPI 和 get_openapi 函数
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

APP_DESCRIPTION = """
## 概述

统一业务 API。成功时 `code = 200`，失败时 `code` 为 HTTP 状态码，响应外壳为：

```json
{ "code": 200, "message": "success", "data": {} }
```

## 鉴权（OAuth2 Password + JWT）

1. 登录 / 注册使用表单：`Content-Type: application/x-www-form-urlencoded`
   - `POST /api/auth/login`（字段 `username`、`password`）
   - `POST /api/auth/register`（字段 `username`、`password`）
   - 或 `POST /api/auth/token`（Swagger Authorize / OAuth2 Password）
2. 受保护接口依赖 `OAuth2PasswordBearer`，请求头携带：

```http
Authorization: Bearer <access_token>
```

也可在 Swagger 右上角 **Authorize**，使用 OAuth2 Password 流程（用户名/密码）自动取 token。

JWT 无状态，过期后需重新登录；退出登录由客户端清除本地 token。

## 静态资源

本地文件目录挂载在 `/static`（可用环境变量 `STATIC_URL` / `STATIC_DIR` 调整）。

例如包内文件 `fastapi_app/static/uploads/demo.png` 对应访问地址：

```text
http://localhost:8000/static/uploads/demo.png
```

## 演示账号

- 用户名：`demo`
- 密码：`123456`
""".strip()

# name 必须与各路由 tags 完全一致，顺序即文档中的分组顺序。
OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "健康检查",
        "description": "服务探活，不依赖数据库与 Redis。",
    },
    {
        "name": "登录模块",
        "description": "注册与登录使用 x-www-form-urlencoded；登录成功后签发 JWT。",
    },
    {
        "name": "用户信息模块",
        "description": "当前用户资料查询与修改、头像上传，以及按 id 查看用户公开信息。",
    },
    {
        "name": "通知模块",
        "description": "当前用户的通知列表、创建通知、标记已读。",
    },
]

# 需要登录的路径（补充 OAuth2 安全要求；Depends(oauth2_scheme) 也会写入 schema）。
_PROTECTED_PATH_PREFIXES = (
    "/api/users/me",
    "/api/notifications",
)


def setup_openapi(app: FastAPI) -> None:
    """
    设置 OpenAPI
    :param app: FastAPI 应用
    :return: None
    """
    def custom_openapi() -> dict:
        """
        自定义 OpenAPI
        :return: dict
        """
        # 如果 OpenAPI 模式已经存在，则返回
        if app.openapi_schema:
            return app.openapi_schema

        # 获取 OpenAPI 模式
        schema = get_openapi(
            # 应用名称
            title=app.title,
            # 应用版本
            version=app.version,
            # 应用描述
            description=app.description,
            # 路由
            routes=app.routes,
            # OpenAPI 标签
            tags=OPENAPI_TAGS,
        )
        # 获取组件
        components = schema.setdefault("components", {})
        # 获取安全方案
        security_schemes = components.setdefault("securitySchemes", {})
        # 覆盖/补齐：Swagger 可用账号密码直接换 token。
        security_schemes["OAuth2PasswordBearer"] = {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/token",
                    "scopes": {},
                }
            },
        }
        # 覆盖/补齐：Swagger 可用账号密码直接换 token。
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "直接粘贴 JWT（login/token 返回的 access_token）。",
        }
        # 遍历路径
        for path, methods in schema.get("paths", {}).items():
            if not path.startswith(_PROTECTED_PATH_PREFIXES):
                continue
            # 遍历方法
            for operation in methods.values():
                if isinstance(operation, dict):
                    # 设置安全
                    operation["security"] = [
                        {"OAuth2PasswordBearer": []},
                        {"BearerAuth": []},
                    ]

        # 设置 OpenAPI 模式
        app.openapi_schema = schema
        return app.openapi_schema

    # 设置 OpenAPI
    app.openapi = custom_openapi  # type: ignore[method-assign]
