# -*-coding:utf-8 -*-

from .views import (
    flow_definition_list_view,
    flow_definition_page_list_view,
    flow_definition_detail_view,
    flow_definition_save_view,
    flow_definition_export_view,
    flow_definition_import_view,
    flow_definition_publish_view,
    flow_definition_toggle_view,
    flow_definition_delete_view,
    flow_perm_pack_list_view,
    flow_user_list_view,
    flow_form_library_detail_view,
    flow_form_library_save_view,
    flow_form_runtime_resolve_view,
)

apis = {
    "": [
        ("A0", "flow_definition_list", flow_definition_list_view.View, "flow template options"),
        ("A1", "flow_definition_page_list", flow_definition_page_list_view.View, "flow definition list"),
        ("A2", "flow_definition_detail", flow_definition_detail_view.View, "flow definition detail"),
        ("A3", "flow_definition_save", flow_definition_save_view.View, "save flow definition"),
        ("A4", "flow_definition_publish", flow_definition_publish_view.View, "publish flow definition"),
        ("A5", "flow_definition_toggle", flow_definition_toggle_view.View, "toggle flow definition"),
        ("A6", "flow_definition_export", flow_definition_export_view.View, "export flow json"),
        ("A7", "flow_definition_import", flow_definition_import_view.View, "import flow json"),
        ("A8", "flow_definition_delete", flow_definition_delete_view.View, "delete flow definition"),
        ("A9", "perm_pack_list", flow_perm_pack_list_view.View, "permission packs"),
        ("A10", "user_list", flow_user_list_view.View, "users"),
        ("A11", "form_library_detail", flow_form_library_detail_view.View, "flow form library detail"),
        ("A12", "form_library_save", flow_form_library_save_view.View, "save flow form library"),
        ("A13", "form_runtime_resolve", flow_form_runtime_resolve_view.View, "resolve runtime form data"),
    ],
}
