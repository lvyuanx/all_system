# 表单设计器默认值与流程上下文能力 PRD

## 1. 文档信息
- 文档版本: v1.0
- 创建日期: 2026-04-10
- 需求状态: 待评审
- 适用范围: `flow_engine` 表单设计器 + 流程运行页（如订单流程）

## 2. 背景与问题
当前节点表单支持基础组件与静态 `default`，并可在审批时将 `form_data` 合并到流程实例 `context`。但仍存在以下缺口：
- 默认值来源能力不足，无法直接从数据库、流程上下文、枚举中获取。
- 字段和上下文的绑定规则不清晰，跨节点复用/改写能力弱。
- 运行时默认值解析主要在前端，缺少统一服务端解析与安全约束。

## 3. 目标与非目标
### 3.1 目标
- 支持字段默认值来源：数据库、流程上下文、枚举。
- 支持节点表单数据按配置写入流程上下文。
- 支持下一个节点读取上下文并可改写后再写回。
- 形成可扩展的字段配置协议，兼容现有 `form_schema`。

### 3.2 非目标
- 本期不做复杂脚本编排平台（仅保留现有字段级 js 能力）。
- 本期不支持任意 SQL 直连执行（需通过受控数据源配置）。
- 本期不改造流程条件表达式引擎（继续使用现有 `SafeEvaluator`）。

## 4. 角色与核心场景
- 流程设计人员：在设计器中配置字段默认值来源和上下文绑定。
- 节点处理人：打开节点表单时看到已解析默认值，提交后写入上下文。
- 后续节点处理人：可读取上游节点数据作为默认值，也可修改并覆盖。

核心场景：
1. 节点 A 的“客户等级”默认值来自数据库查询。
2. 节点 B 的“审核金额”默认值来自 `context.form.NODE_A.amount`。
3. 节点 C 的“处理意见类型”选项来自枚举，默认值为枚举中 `default=true` 项。
4. 节点 D 修改了从节点 B 继承的字段，并覆盖回上下文。

## 5. 功能需求
### 5.1 字段默认值来源
每个字段新增 `default_config`：
- `source_type`: `literal | context | enum | db`
- `value`: 当 `literal` 时使用
- `context_path`: 当 `context` 时读取路径
- `enum_code` / `enum_value_key`: 当 `enum` 时读取
- `db_source_code` / `db_params`: 当 `db` 时读取
- `fallback_value`: 默认值获取失败时兜底值

默认值解析优先级：
1. 若上下文已存在该字段绑定路径值（历史已填写/已改写），优先使用上下文值。
2. 否则按 `default_config.source_type` 拉取默认值。
3. 拉取失败或为空时使用 `fallback_value`。
4. 仍无值时按组件类型给空值（与现逻辑一致）。

### 5.2 字段选项来源（select/radio/checkbox）
每个可选项字段新增 `options_config`：
- `source_type`: `manual | enum | db | context`
- `manual_options`: 手工选项（兼容现有 `options`）
- `enum_code` / `db_source_code` / `context_path`
- `label_key` / `value_key`

要求：
- 若配置了动态来源，运行时优先动态来源。
- 动态来源失败时可回退到手工选项（可配置 `fallback_to_manual=true`）。

### 5.3 表单数据写入上下文
每个字段新增 `context_binding`：
- `read_path`: 读取路径（可为空，为空则默认 `${node_scope}.${field_key}`）
- `write_path`: 写入路径（可为空，为空则默认 `${node_scope}.${field_key}`）
- `write_mode`: `overwrite | merge_if_absent`

节点作用域约定：
- 默认 `node_scope = form.<node_code>`。
- 本期统一写入 `instance.context`（JSON）中。

审批提交时：
- `action=approve` 的 `form_data` 与字段 `context_binding` 合并写入上下文。
- 写入成功后，后续节点可通过 `context_path/read_path` 读取。

### 5.4 节点间读取与改写
- 下游节点字段可将 `default_config.source_type=context` 指向上游路径。
- 下游节点可将 `write_path` 指向同一路径，实现“读取后改写”。
- 改写策略：
  - `overwrite`: 直接覆盖。
  - `merge_if_absent`: 仅在目标路径无值时写入。

### 5.5 设计器交互需求
在字段配置抽屉新增：
- “默认值来源”区域：来源类型、来源参数、兜底值。
- “选项来源”区域（仅可选项组件显示）。
- “上下文绑定”区域：读取路径、写入路径、写入策略。
- “变量路径选择器”：展示当前上下文可用路径（含 `form.*`、业务基础字段）。

校验规则：
- `source_type=context` 时必须填写 `context_path`。
- `source_type=enum` 时必须选择 `enum_code`。
- `source_type=db` 时必须选择受控 `db_source_code`。
- `write_path/read_path` 必须是合法点路径（`a.b.c`）。

## 6. 数据结构设计
### 6.1 字段 Schema 扩展（示例）
```json
{
  "key": "amount",
  "label": "审核金额",
  "component": "number",
  "required": true,
  "default": 0,
  "default_config": {
    "source_type": "context",
    "context_path": "form.NODE_A.amount",
    "fallback_value": 0
  },
  "context_binding": {
    "read_path": "form.NODE_A.amount",
    "write_path": "form.NODE_B.amount",
    "write_mode": "overwrite"
  }
}
```

### 6.2 上下文结构建议
```json
{
  "order_id": 1001,
  "order_no": "SO20260410001",
  "form": {
    "NODE_A": {
      "amount": 1280,
      "customer_level": "vip"
    },
    "NODE_B": {
      "amount": 1500,
      "audit_comment": "调增"
    }
  }
}
```

## 7. 接口与后端改造
### 7.1 现有接口延展
- `POST /order/workflow_action`
  - 继续接收 `form_data`。
  - 服务端按字段 `context_binding` 写入上下文（不再只做平铺 merge）。

### 7.2 新增运行时解析接口（建议）
- `GET /flow_engine/form_runtime_resolve`
- 入参：`instance_id`, `task_id`（或 `node_code`）
- 出参：
  - `resolved_fields`: 含已解析默认值、选项、只读状态
  - `context_snapshot`: 当前上下文快照（脱敏后）

### 7.3 数据源与枚举服务
- 枚举：复用系统枚举服务，统一 `enum_code -> [{label,value,default}]`。
- 数据库来源：仅允许选择白名单数据源 `db_source_code`，由后端预置查询模板 + 参数映射执行。

## 8. 安全与性能
- 禁止前端直接传 SQL，数据库默认值/选项必须由后端受控模板执行。
- `context` 读取按实例权限校验，避免越权读取。
- 单节点默认值解析接口响应时间目标 P95 < 300ms（不含慢查询告警）。
- 数据源查询增加超时与缓存（建议 30~120 秒可配置）。

## 9. 兼容性与迁移
- 旧表单 `form_schema` 无 `default_config/context_binding/options_config` 时，沿用当前逻辑。
- 兼容已有字段 `default`、`options`。
- 渐进式迁移：新建流程优先使用新配置，历史流程按版本保持不变。

## 10. 验收标准（UAT）
1. 字段默认值可从数据库、上下文、枚举分别成功加载。
2. 同一字段同时存在“上下文已有值”和“默认来源”时，优先显示上下文已有值。
3. 节点 A 提交后，节点 B 能读取到 A 写入的上下文值。
4. 节点 B 修改同字段并提交后，节点 C 读取到修改后的值。
5. 动态选项加载失败时，按配置正确回退到手工选项。
6. 非法数据源配置/无权限读取时，接口返回明确错误码，不泄露底层 SQL。
7. 不配置新能力的旧流程，表现与当前版本一致。

## 11. 里程碑建议
- M1（2~3 天）: Schema 扩展 + 设计器配置 UI。
- M2（3~5 天）: 运行时解析服务 + 数据源/枚举接入。
- M3（2~3 天）: 提交写回策略 + 节点间改写链路。
- M4（1~2 天）: 回归测试 + 灰度发布。

## 12. 风险与待确认
- 是否允许“多个节点写同一路径”默认开启；如开启需审计日志增强。
- `context` 命名空间是否强制 `form.<node_code>`，或允许业务自定义根路径。
- 数据源白名单由谁维护（研发配置 vs 管理后台配置）。
