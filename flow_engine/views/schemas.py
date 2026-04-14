# -*-coding:utf-8 -*-

from typing import Any
from pydantic import BaseModel, Field


class FlowNodeRuleSchema(BaseModel):
    rule_type: str = Field(..., description="rule_type: perm_pack/user")
    perm_pack_id: int | None = Field(None, description="permission pack id")
    user_id: int | None = Field(None, description="user id")


class FlowNodeGroupSchema(BaseModel):
    key: str = Field(..., description="group key")
    name: str | None = Field(None, description="group name")
    min_approve_count: int = Field(1, description="min approve count")
    order: int = Field(0, description="order")
    rules: list[FlowNodeRuleSchema] = Field(default_factory=list, description="rules")


class FlowNodeSchema(BaseModel):
    code: str = Field(..., description="node code")
    name: str = Field(..., description="node name")
    node_type: str = Field(..., description="node type")
    approval_mode: str = Field("any", description="approval mode")
    is_auto: bool = Field(False, description="is auto")
    order: int = Field(0, description="order")
    form_schema: dict[str, Any] | None = Field(None, description="form schema")
    groups: list[FlowNodeGroupSchema] = Field(default_factory=list, description="groups")


class FlowTransitionSchema(BaseModel):
    source_code: str = Field(..., description="source node code")
    target_code: str = Field(..., description="target node code")
    condition_expr: str | None = Field(None, description="condition json")
    description: str | None = Field(None, description="description")


class FlowFormDefinitionSchema(BaseModel):
    code: str = Field(..., description="form code")
    name: str = Field(..., description="form name")
    group_name: str | None = Field(None, description="form group name")
    description: str | None = Field(None, description="form description")
    fields: list[dict[str, Any]] = Field(default_factory=list, description="form fields")
    order: int = Field(0, description="form order")


class GlobalFormLibraryItemSchema(FlowFormDefinitionSchema):
    form_id: int = Field(..., description="form id")
    bind_flow_count: int = Field(0, description="bound flow count")
    field_count: int = Field(0, description="field count")
    bind_node_count: int = Field(0, description="bound node count")
    is_active: bool = Field(True, description="form active")
    update_time_str: str | None = Field(None, description="update time")


class FlowDefinitionSaveSchema(BaseModel):
    flow_id: int | None = Field(None, description="flow id")
    code: str = Field(..., description="flow code")
    name: str = Field(..., description="flow name")
    description: str | None = Field(None, description="description")
    is_active: bool = Field(True, description="active")
    nodes: list[FlowNodeSchema] = Field(default_factory=list, description="nodes")
    transitions: list[FlowTransitionSchema] = Field(default_factory=list, description="transitions")
    form_library: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form library")


class FlowDefinitionDetailSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")
    code: str = Field(..., description="flow code")
    name: str = Field(..., description="flow name")
    description: str | None = Field(None, description="description")
    is_active: bool = Field(True, description="active")
    nodes: list[FlowNodeSchema] = Field(default_factory=list, description="nodes")
    transitions: list[FlowTransitionSchema] = Field(default_factory=list, description="transitions")
    form_library: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form library")


class FlowPermPackItemSchema(BaseModel):
    pack_id: int = Field(..., description="pack id")
    pack_code: str = Field(..., description="pack code")
    pack_name: str = Field(..., description="pack name")


class FlowUserItemSchema(BaseModel):
    user_id: int = Field(..., description="user id")
    full_name: str | None = Field(None, description="full name")
    phone: str | None = Field(None, description="phone")


class FlowDefinitionListItemSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")
    code: str = Field(..., description="flow code")
    name: str = Field(..., description="flow name")
    version: str | None = Field(None, description="current version label")
    is_active: bool = Field(True, description="active")
    bind_order_count: int = Field(0, description="bound order count")
    create_time_str: str | None = Field(None, description="create time")
    update_time_str: str | None = Field(None, description="update time")


class FlowDefinitionToggleSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")
    is_active: bool = Field(..., description="active")


class FlowDefinitionImportSchema(BaseModel):
    overwrite: bool = Field(False, description="overwrite existing definition by code")
    payload: FlowDefinitionSaveSchema = Field(..., description="flow json payload")


class FlowDefinitionActionRespSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")


class FlowDefinitionDeleteSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")


class FlowFormLibraryDetailSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")
    code: str = Field(..., description="flow code")
    name: str = Field(..., description="flow name")
    forms: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form definitions")


class FlowFormLibrarySaveSchema(BaseModel):
    flow_id: int = Field(..., description="flow id")
    forms: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form definitions")


class GlobalFormLibraryDetailSchema(BaseModel):
    forms: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form definitions")


class GlobalFormLibrarySaveSchema(BaseModel):
    forms: list[FlowFormDefinitionSchema] = Field(default_factory=list, description="form definitions")


class FlowFormRuntimeResolveSchema(BaseModel):
    instance_id: int = Field(..., description="flow instance id")
    task_id: int | None = Field(None, description="task id")


class FlowFormRuntimeResolveRespSchema(BaseModel):
    instance_id: int = Field(..., description="flow instance id")
    node_code: str = Field("", description="node code")
    node_name: str = Field("", description="node name")
    resolved_form_schema: Any = Field(default_factory=dict, description="resolved form schema")
    resolved_form_data: dict[str, Any] = Field(default_factory=dict, description="resolved form data")
    context_snapshot: dict[str, Any] = Field(default_factory=dict, description="current context")


class FlowFormRuntimePreviewResolveSchema(BaseModel):
    form_schema: Any = Field(..., description="form schema")
    context: dict[str, Any] | None = Field(None, description="context snapshot")
    node_code: str | None = Field("", description="node code")
    runtime_env: dict[str, Any] | None = Field(None, description="runtime env")


class FlowFormRuntimePreviewResolveRespSchema(BaseModel):
    resolved_form_schema: Any = Field(default_factory=dict, description="resolved form schema")
    resolved_form_data: dict[str, Any] = Field(default_factory=dict, description="resolved form data")
    context_snapshot: dict[str, Any] = Field(default_factory=dict, description="context snapshot")


class FieldDataSourceMetadataItemSchema(BaseModel):
    key: str = Field(..., description="data source key")
    label: str = Field(..., description="data source label")
    data_type: str = Field(..., description="data type")
    support_components: list[str] = Field(default_factory=list, description="supported components")
    supported_methods: list[str] = Field(default_factory=list, description="component-specific datasource methods")


class FieldDataSourceMetadataRespSchema(BaseModel):
    items: list[FieldDataSourceMetadataItemSchema] = Field(default_factory=list, description="data source metadata")
