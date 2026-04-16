# core.ninja_extra

## 模块定位
- `core.ninja_extra` 是项目自己的 API 框架层。
- 它基于 `django-ninja` 做了重写式增强，不是简单薄封装。
- 负责统一 API 注册、响应结构、异常处理、错误码、权限包装、分页和文档输出。

## 关键文件
- `api_extra.py`：`BaseApi`、路由注册、接口包装核心
- `urls.py`：API 入口与文档路由
- `response_schema.py`：统一响应结构
- `exception_handlers.py`：统一异常处理
- `base_pagination.py`：统一分页能力
- `docs_extra.py`：文档页增强

## 通用约定
- 在 Django template 中使用 Vue 时，统一沿用 `[[ ]]` 作为插值分隔符，避免和 Django 的 `{{ }}` 冲突。
- 单个文件尽量不要超过 `500` 行；如果明显超出，应优先按职责拆分。

## 修改约束
- 这里是框架层，任何改动都可能影响全项目 API。
- 不要轻易改变：
  - `BaseApi` 调用方式
  - 响应结构
  - 错误码生成逻辑
  - 路由聚合方式
- 改动前优先检查 `main/apis.py` 和现有各 app 的 `apis.py`。

## 验证建议
- 重点验证：
  - API 注册是否正常
  - Swagger / OpenAPI 是否正常
  - 成功/失败响应是否兼容
  - 分页与权限包装是否正常
