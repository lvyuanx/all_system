# 表单设计器数据源类机制说明

## 适用范围

本说明对应 `flow_engine` 中表单设计器和流程设计器共用的字段数据源机制，覆盖：

- 运行时解析：`flow_engine/utils/form_runtime_util.py`
- 设计器示例：`flow_engine/utils/form_designer_data_source_examples.py`
- 元数据接口：`flow_engine/page_views/flow_page.py`

## 配置约定

字段默认值和选项列表同时支持新旧两套配置，并保持向后兼容：

- 默认值：
  - 新配置：`default_source_config`
  - 旧配置：`default_config`
- 选项：
  - 新配置：`options_source_config`
  - 旧配置：`options_config`

运行时优先级如下：

1. 优先解析 `default_source_config` / `options_source_config`
2. 新配置缺失、数据源未注册或返回空结果时，再按回退规则处理
3. 最后继续兼容旧版 `default_config` / `options_config`

这意味着旧表单无需迁移即可继续工作，新表单可以逐步切换到数据源类机制。

## 内置数据源类

当前内置了以下数据源类：

- `ctx_text`：从流程上下文按路径读取单值，适用于默认值
- `order_field_text`：按订单字段读取单值，适用于默认值
- `site_address_select`：按订单所属站点加载地址选项，适用于选项列表

设计器中展示的“内置数据源示例”只是旧配置参考样例；运行时实际数据源类元信息来自注册中心。

## 自定义数据源类开发

自定义类需继承 `BaseFieldDataSource`，并至少声明：

- `key`
- `label`
- `data_type`
- `support_components`
- `support_default`
- `support_options`

如需在设计器中渲染参数表单，可提供 `params_schema`，每项至少包含：

- `name`
- `label`
- `target`
- `component`

运行时会为数据源实例注入以下上下文：

- `self.ctx`
- `self.request`
- `self.field_schema`
- `self.instance`
- `self.node_code`
- `self.runtime_env`

常见实现方式：

```python
from flow_engine.utils.form_runtime_util import BaseFieldDataSource, _MISSING


class ExampleDefaultSource(BaseFieldDataSource):
    key = "example_default"
    label = "示例默认值"
    data_type = "text"
    support_components = ["input"]
    support_default = True

    def get_default(self, request):
        value = self.get_ctx_value("form.NODE_A.code", _MISSING)
        return value
```

注册方式使用 Django setting `FLOW_ENGINE_FIELD_DATA_SOURCES`，可传类路径或类对象。

## 元数据接口

接口：`/admin/flow_engine/field_data_sources/metadata/`

返回字段：

- `key`
- `label`
- `data_type`
- `support_components`
- `support_default`
- `support_options`
- `params_schema`

设计器依赖该接口过滤当前字段组件可用的数据源类，并动态渲染参数配置项。
