# Form Designer 说明

## 目录定位
- 当前目录：`flow_engine/templates/flow_engine/form_designer/`
- 这是表单设计器模板目录。
- 主模板入口：`index.html`
- 局部模板：
  - `_preview_dialog.html`
  - `_field_data_source_dialog.html`
  - `_json_dialog.html`

## form_designer 是什么
- `form_designer` 是流程引擎中的表单设计器页面。
- 它用于维护流程表单库，支持新增表单、拖拽组件、编辑字段属性、配置默认值/选项数据源、预览运行效果、导入导出 JSON。
- 页面由 Django 模板承载，前端交互主要由 Vue 运行时脚本完成。

## 页面与资源对应关系
- Django 渲染入口：`flow_engine/form_designer/index.html`
- 后端页面入口：
  - `flow_engine.page_views.flow_page.flow_form_designer`
  - `flow_engine.page_views.flow_page.flow_form_global_designer`
- 前端 JS 入口：`oss/static/flow_engine/js/form_designer.js`
- 实际运行时：`oss/static/flow_engine/js/form_designer_runtime.js`
- 表单设计器样式：`oss/static/flow_engine/css/form_designer.css`

## 前端模块拆分
- `form_designer.js`
  - 对外稳定入口，仅做转发，避免模板 import 路径频繁变动。
- `form_designer_runtime.js`
  - 表单设计器主运行时，负责页面状态、表单树操作、保存、预览、JSON 导入导出等。
- `form_designer_constants.js`
  - 组件分组、组件别名、组件标签、展示类组件集合等常量。
- `form_designer_style.js`
  - 文本、分割线、间距块、卡片、容器等样式拼装函数。
- `form_designer_component_preview.js`
  - 设计态组件预览。
- `form_designer_designer_node_item.js`
  - 设计器画布中的节点递归渲染。
- `form_designer_preview_field_render.js`
  - 运行预览态字段渲染。
- `form_designer_field_sources.js`
  - 字段数据源选择器、数据源元信息获取、参数联动逻辑。

## 修改时必须遵守
- 不要随意改变现有业务逻辑、字段协议、接口路径、URL 参数语义。
- 优先保持 `oss/static/flow_engine/js/form_designer.js` 这个公开入口不变。
- 如果移动模板，必须同步更新：
  - `flow_engine/page_views/flow_page.py`
  - `flow_engine/tests.py`
- 如果修改了模板中的静态资源路径或版本号，确认对应静态文件真实存在。
- 如果拆分新的前端模块，优先做“小模块 + 运行时组装”，不要把逻辑重新塞回单文件。

## 验证建议
- 前端模块测试：
  - `node --test flow_engine/tests_form_designer_modules.test.mjs`
  - `node --test flow_engine/tests_field_source_designer.test.mjs`
- Django 测试：
  - `python manage.py test flow_engine.tests`
- 注意：当前环境如果没有安装 Django，`python manage.py test` 会直接失败，需要先切换到正确虚拟环境。

## 当前已知情况
- 表单设计器模板已经集中到本目录。
- 主模板使用 include 引入局部弹窗模板。
- 样式已从模板内联 `<style>` 抽离到独立 CSS 文件。
