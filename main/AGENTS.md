# main

## 模块定位
- `main` 是 Django 项目的主入口模块。
- 它负责全局配置、URL 汇总、API 汇总、WSGI/ASGI 入口和首页入口。
- 这里承载的是项目级装配逻辑，而不是具体业务实现。

## 目录说明
- `settings.py`
  - Django 全局配置入口
  - 包含 `INSTALLED_APPS`、中间件、模板、数据库、静态资源、Ninja 相关配置
- `urls.py`
  - 项目主 URL 汇总
  - 汇总后台页面路由与 API 路由
- `apis.py`
  - 项目 API 聚合入口
  - 通过 `core.ninja_extra` 的约定汇总各业务模块 API 和移动端 API
- `asgi.py` / `wsgi.py`
  - 部署入口
- `page_views/`
  - 项目级页面入口，例如首页
- `templates/`
  - 项目级模板
- `init/`
  - 初始化相关逻辑或预留目录

## 通用约定
- 在 Django template 中使用 Vue 时，统一沿用 `[[ ]]` 作为插值分隔符，避免和 Django 的 `{{ }}` 冲突。
- 单个文件尽量不要超过 `500` 行；如果明显超出，应优先按职责拆分。

## 修改约束
- 不要把具体业务逻辑直接写进 `main`。
- `main` 更适合承载：
  - 全局配置
  - 路由装配
  - API 聚合
  - 项目级入口页面
- 修改 `settings.py` 时要特别谨慎，可能影响全项目。
- 修改 `urls.py` 时要确认：
  - 后台页面入口是否仍可访问
  - API 路由是否仍被正确挂载
- 修改 `apis.py` 时要遵循 `core.ninja_extra` 既有聚合方式，不要破坏全局 API 编排结构。

## 验证建议
- 重点检查：
  - Django 是否能正常启动
  - 后台首页与 `/admin/` 是否正常访问
  - API 根路径是否正常挂载
  - Swagger / OpenAPI 文档是否正常
- 常用验证命令：
  - `python manage.py check`
  - `python manage.py test`

## 补充说明
- `main` 是项目装配层，不是业务层。
- 如果一个改动只影响某个业务域，应优先放在对应业务 app，而不是直接改 `main`。
