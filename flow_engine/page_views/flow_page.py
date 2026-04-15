# -*-coding:utf-8 -*-

from django.http import JsonResponse
from django.shortcuts import render

from flow_engine.utils.form_designer_data_source_examples import (
    get_builtin_form_data_source_examples,
)
from flow_engine.utils.form_runtime_util import (
    build_field_data_source_metadata_payload,
    get_registered_field_data_source_metadata,
)


def _build_designer_context(**extra):
    context = {
        "builtin_data_source_examples": get_builtin_form_data_source_examples(),
        "field_data_source_metadata": get_registered_field_data_source_metadata(),
    }
    context.update(extra)
    return context


def flow_definition_add(request):
    context = _build_designer_context(
        title="流程设计器",
        flow_id="",
    )
    return render(request, "flow_engine/flow_designer/index.html", context)


def flow_definition_change(request, fid: int):
    context = _build_designer_context(
        title="流程设计器",
        flow_id=fid,
    )
    return render(request, "flow_engine/flow_designer/index.html", context)


def flow_definition_list(request):
    return render(request, "flow_engine/flow_list.html", {"title": "流程列表"})


def flow_form_designer(request, fid: int):
    context = _build_designer_context(
        title="表单设计器",
        flow_id=fid,
        previous_url=f"/admin/flow_engine/definition/{fid}/change/",
    )
    return render(request, "flow_engine/form_designer/index.html", context)


def flow_form_global_designer(request):
    context = _build_designer_context(
        title="表单设计器",
        flow_id="",
        previous_url="/admin/flow_engine/form/list/",
    )
    return render(request, "flow_engine/form_designer/index.html", context)


def flow_form_list(request):
    return render(request, "flow_engine/form_list.html", {"title": "表单列表"})


def field_data_source_metadata(request):
    return JsonResponse(build_field_data_source_metadata_payload())
