# 项目总览

## 项目定位
- 项目根目录：`D:\projects\all_system`
- 这是一个以 **Django** 为核心的业务系统。
- 整体架构可以理解为：
  - `Django`：后端主框架，负责模型、路由、模板、接口、业务逻辑
  - `Django Admin / SimpleUI`：后台管理端，承担大部分内部运营与配置页面
  - `移动端`：主要通过后端提供的移动端 API 访问业务能力，而不是在本仓库中维护一套完整的前端 App 工程

## 核心设计原则
- `core` 是这套系统的**框架核心层**，设计目标是高通用、低业务耦合。
- `core` 不应承载具体业务语义，它更像一个可以迁移到其他 Django 系统中的基础框架包。
- 业务模块应尽量建立在 `core` 提供的能力之上，而不是反向把业务逻辑塞回 `core`。
- 从当前目录结构看，`staff`、`order`、`bill`、`client_mgmt`、`flow_engine`、`pattern_library` 等都属于业务层；`core` 则属于底层能力层。

## 架构概况
- 主配置入口：
  - `manage.py`
  - `main/settings.py`
  - `main/urls.py`
- 后端使用 Django 模板系统，同时在部分后台页面中使用 Vue 3 + Element Plus 增强交互。
- 管理后台基于 Django Admin，并使用 `simpleui` 做后台主题与交互增强。
- 移动端能力主要以 API 形式暴露，例如 `order/mobile_apis.py` 中定义了移动端订单相关接口。

## API 框架说明
- 项目虽然依赖了 `ninja`，但后端 API 层并不是“直接原生使用 Django Ninja”。
- 当前实现是基于 `core.ninja_extra` 对 Ninja 做了一套**重写式增强**，它已经是项目自己的 API 基础框架。
- 这层增强的核心作用包括：
  - 基于 `ROOT_APICONF` 自动汇总并注册全项目 API
  - 用统一的 `apis = [...] / apis = {...}` 配置组织路由与接口分组
  - 通过 `BaseApi` 统一接口写法，而不是零散直接写原生 Ninja 视图
  - 统一成功/失败响应结构
  - 统一异常包装与业务异常输出
  - 统一接口错误码拼装逻辑
  - 统一权限包装
  - 统一分页能力
  - 对 Swagger / OpenAPI 文档做了项目级改造
- 关键实现位置：
  - `core/ninja_extra/api_extra.py`
  - `core/ninja_extra/urls.py`
  - `core/ninja_extra/response_schema.py`
  - `core/ninja_extra/exception_handlers.py`
  - `core/ninja_extra/base_pagination.py`
  - `main/apis.py`
- 因此在这个项目里，可以把 `core.ninja_extra` 理解为：
  - “项目自己的 API 框架层”
  - 而不是简单的第三方库薄封装

## 主要模块分层
- `core`
  - 框架核心层，强调通用性、可移植性、低业务耦合。
  - 包含认证基础、公共能力、中间件、工具类、API 扩展框架、后台增强能力等。
- `main`
  - 项目主配置与全局入口，包含 settings、urls、首页等。
- `system`
  - 系统级数据或预留模块。
- `staff`
  - 员工管理相关业务。
- `bill`
  - 票据、账单相关业务。
- `client_mgmt`
  - 客户管理相关业务。
- `order`
  - 订单管理核心模块，同时包含移动端订单 API。
- `site_mgmt`
  - 站点、多租户或站点上下文相关能力。
- `flow_engine`
  - 流程引擎相关能力，包含流程设计器、表单设计器、运行时数据源等。
- `pattern_library`
  - 版式/模板库相关业务。
- `oss`
  - 静态资源与媒体文件目录。

## 前端形态
- 传统后台页面：
  - Django 模板 + Admin 页面为主
- 增强型后台页面：
  - Django 模板中通过 `<script type="module">` 挂载 Vue 3
  - 这类页面很多直接写在 Admin / Django template 中
  - 由于 Django 模板本身使用 `{{ }}`，为了避免和 Vue 默认插值语法冲突，项目中 Vue 通常统一把分隔符改为 `[[ ]]`
  - 因此在这类模板里看到 `[[ value ]]`，应理解为 Vue 渲染，不是 Django 模板语法
  - 静态资源位于 `oss/static/`
  - 常见资源：
    - `oss/static/vue/`
    - `oss/static/element-plus/`
    - `oss/static/flow_engine/`
- 移动端：
  - 当前仓库中重点是“移动端接口”，而不是完整独立的移动端前端工程
  - 典型入口：`order/mobile_apis.py`

## 页面验证要求
- 涉及后台页面、Django 模板、Vue 页面、Admin 交互、下拉框/弹窗/表格/图表等前端行为时，如果有必要，优先使用 **Playwright MCP** 或等价浏览器自动化方式直接打开页面验证真实表现，不要只凭代码静态阅读或主观猜测下结论。
- 尤其是在以下场景，必须优先做页面实测后再判断：
  - 用户明确说“页面表现不对”“你自己上页面看”
  - 改动涉及表单交互、选项渲染、权限显隐、异步加载、联动筛选
  - 服务端模板与浏览器实际表现可能不一致时
- 如果本地后台可登录，默认可使用以下账号进行验证：
  - 用户名：`admin`
  - 密码：`123456`
- 若 Playwright MCP / 浏览器工具当前不可用，应先说明受限原因，再选择次优验证方式；不要在未实测的情况下把推断当成事实。

## 目录速览
- `core/`
  - 框架核心代码、中间件、认证、API 扩展、公共工具
- `main/`
  - Django 项目主配置
- `flow_engine/`
  - 流程/表单设计器、流程运行相关功能
- `order/`
  - 订单后台与移动端接口
- `oss/static/`
  - 前端静态资源
- `oss/media/`
  - 上传文件、媒体资源
- `docs/`
  - 项目文档
- `docker/`
  - 容器化构建相关文件
- `run/`
  - 脚本、SQL、部署辅助内容

## 开发约束
- 优先保持现有业务逻辑、接口协议、模板路径语义不变。
- 单个文件尽量不要超过 `500` 行。
- 如果文件明显超过 `500` 行，应优先考虑拆分，而不是继续堆叠内容。
- 拆分时优先按职责边界拆分，例如：
  - 模板入口 / partial
  - JS facade / runtime / constants / manager
  - 通用能力 / 业务能力
- 对 `core` 的修改要非常克制：
  - 只有当需求属于“框架级通用能力”时，才应该落到 `core`
  - 如果需求明显带有业务属性，应优先放到对应业务模块
- 这是一个“后端主导”的项目，做前端调整时要先确认 Django 模板、静态资源路径、页面渲染入口是否同步更新。
- 在 Django template 中写 Vue 时，不要误用默认 `{{ }}` 插值。
- 这类页面应优先沿用现有约定的 Vue 分隔符 `[[ ]]`，否则容易和 Django 模板语法冲突。
- 若移动模板位置，必须同步检查：
  - `render(...)` 引用路径
  - `get_template(...)` 测试引用
  - 模板中的 `{% include %}` 路径
- 若拆分前端模块，优先保留稳定 facade 入口，避免模板直接依赖深层模块。
- 对 API 层的修改优先遵循 `core.ninja_extra` 既有模式：
  - 先看 `BaseApi`
  - 再看 `main/apis.py` 的路由聚合方式
  - 不要绕开这层框架直接零散注册原生 Ninja 路由，除非确有充分理由

## 当前已知实现方式
- Django 已安装应用可在 `main/settings.py` 的 `INSTALLED_APPS` 查看。
- 后台主题使用 `simpleui`。
- 中间件中包含 JWT、后台登录态转换、菜单注入、站点上下文等逻辑。
- 数据库默认配置为 MySQL。
- API 根配置由 `ROOT_APICONF = "main.apis"` 驱动。
- API 文档、异常处理、响应结构、分页能力都已收口到 `core.ninja_extra`。

## 验证建议
- Django 测试：
  - `python manage.py test`
  - 或按模块执行，例如 `python manage.py test flow_engine.tests`
- 前端模块测试：
  - 当前部分模块使用 `node --test`
- 如果 `python manage.py test` 报缺少 Django，先切换到正确虚拟环境，例如 `.venv`

## 给后续 Agent 的建议
- 修改前先确认自己改的是：
  - 后台页面模板
  - 后台管理逻辑
  - API 层
  - 移动端接口
- 不要把“移动端”误解为仓库内必须存在独立 App 前端；本项目当前明显存在的是移动端 API 能力。
- 不要把 `core` 当成普通业务 app 使用。
- 如果一个能力未来可以复用到其他系统，并且不依赖具体业务名词，才适合放进 `core`。
- 如果你在改 API，先优先研究：
  - `core/ninja_extra/api_extra.py`
  - `core/ninja_extra/urls.py`
  - `main/apis.py`
- 对 `flow_engine`、`order` 这类模块做结构性重构时，优先补测试，再做文件迁移。
