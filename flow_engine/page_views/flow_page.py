# -*-coding:utf-8 -*-

from django.shortcuts import render

from flow_engine.utils.form_designer_data_source_examples import (
    get_builtin_form_data_source_examples,
)


def _build_designer_context(**extra):
    context = {
        "builtin_data_source_examples": get_builtin_form_data_source_examples(),
    }
    context.update(extra)
    return context


def flow_definition_add(request):
    context = _build_designer_context(
        title="流程设计器",
        flow_id="",
    )
    return render(request, "flow_engine/flow_designer.html", context)


def flow_definition_change(request, fid: int):
    context = _build_designer_context(
        title="流程设计器",
        flow_id=fid,
    )
    return render(request, "flow_engine/flow_designer.html", context)


def flow_definition_list(request):
    context = {
        "title": "流程列表",
    }
    return render(request, "flow_engine/flow_list.html", context)


def flow_form_designer(request, fid: int):
    context = _build_designer_context(
        title="表单设计器",
        flow_id=fid,
    )
    return render(request, "flow_engine/form_designer.html", context)


def flow_form_list(request):
    context = {
        "title": "表单列表",
    }
    return render(request, "flow_engine/form_list.html", context)
