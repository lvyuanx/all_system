# Flow Designer 说明

## 目录定位
- 当前目录：`flow_engine/templates/flow_engine/flow_designer/`
- 这是流程设计器页面模板目录。
- 主模板入口：`index.html`
- 局部模板：
  - `_import_dialog.html`
  - `_field_data_source_dialog.html`
  - `_node_dialog.html`

## flow_designer 是什么
- `flow_designer` 是流程引擎中的流程设计器页面。
- 它用于维护流程定义、节点、连线、节点表单、审批组和规则，并支持保存、发布、导入、导出。
- 页面由 Django 模板承载，前端主逻辑由 Vue 运行时脚本完成。

## 页面与资源对应关系
- Django 模板入口：`flow_engine/flow_designer/index.html`
- 后端入口：
  - `flow_engine.page_views.flow_page.flow_definition_add`
  - `flow_engine.page_views.flow_page.flow_definition_change`
- 前端 JS 入口：`oss/static/flow_engine/js/flow_designer.js`
- 前端运行时：`oss/static/flow_engine/js/flow_designer_runtime.js`
- 常量文件：`oss/static/flow_engine/js/flow_designer_constants.js`
- 样式文件：`oss/static/flow_engine/css/flow_designer.css`

## 当前拆分原则
- 保持原有业务逻辑、接口路径、字段协议不变。
- 主模板尽量只保留页面骨架、include、数据注入和模块入口。
- 对外稳定入口优先保持为 `flow_designer.js`，避免模板频繁改 import。
- 新增 JS 模块时优先按职责拆分，不要把逻辑重新堆回 `index.html`。

## 修改时必须同步
- 如果模板路径变更，必须同步更新：
  - `flow_engine/page_views/flow_page.py`
  - `flow_engine/tests.py`
- 如果静态资源路径或版本号变更，必须确认模板引用和实际文件一致。
- 如果拆节点表单或字段数据源逻辑，优先复用 `field_source_designer.js` 的 helper，不要复制协议实现。

## 验证建议
- 前端模块测试：
  - `node --test flow_engine/tests_flow_designer_modules.test.mjs`
  - `node --test flow_engine/tests_field_source_designer.test.mjs`
- Django 测试：
  - `python manage.py test flow_engine.tests`
- 注意：如果当前解释器没有安装 Django，`python manage.py test` 会失败，需要切换到正确虚拟环境。
