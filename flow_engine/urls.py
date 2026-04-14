from django.urls import path
from .page_views.flow_page import (
    field_data_source_metadata,
    flow_definition_add,
    flow_definition_change,
    flow_definition_list,
    flow_form_designer,
    flow_form_global_designer,
    flow_form_list,
)

urls = [
    path("flow_engine/definition/list/", flow_definition_list, name="flow_definition_list"),
    path("flow_engine/form/list/", flow_form_list, name="flow_form_list"),
    path("flow_engine/form/designer/", flow_form_global_designer, name="flow_form_global_designer"),
    path("flow_engine/definition/add/", flow_definition_add, name="flow_definition_add"),
    path("flow_engine/definition/<int:fid>/change/", flow_definition_change, name="flow_definition_change"),
    path("flow_engine/definition/<int:fid>/form_designer/", flow_form_designer, name="flow_form_designer"),
    path("flow_engine/field_data_sources/metadata/", field_data_source_metadata, name="field_data_source_metadata"),
]
