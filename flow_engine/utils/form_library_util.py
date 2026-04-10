# -*-coding:utf-8 -*-

from copy import deepcopy
from typing import Any


FORM_LIBRARY_KEY = "__form_library"
FORM_REF_CODE_KEY = "__form_ref_code"
FORM_REF_NAME_KEY = "__form_ref_name"


def normalize_form_library(forms: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not isinstance(forms, list):
        return []

    normalized = []
    existed_codes: set[str] = set()
    for index, raw in enumerate(forms):
        if not isinstance(raw, dict):
            continue

        code = str(raw.get("code") or "").strip()
        if not code or code in existed_codes:
            continue
        existed_codes.add(code)

        name = str(raw.get("name") or "").strip() or code
        description = str(raw.get("description") or "").strip()

        fields = raw.get("fields")
        if not isinstance(fields, list):
            fields = []

        try:
            order = int(raw.get("order"))
        except (TypeError, ValueError):
            order = index

        normalized.append(
            {
                "code": code,
                "name": name,
                "description": description,
                "fields": deepcopy(fields),
                "order": order,
            }
        )

    normalized.sort(key=lambda item: (item.get("order", 0), item.get("code", "")))
    for idx, item in enumerate(normalized):
        item["order"] = idx
    return normalized


def extract_form_library(form_schema: Any) -> list[dict[str, Any]]:
    if not isinstance(form_schema, dict):
        return []
    return normalize_form_library(form_schema.get(FORM_LIBRARY_KEY))


def extract_form_library_from_nodes(nodes: list[Any]) -> list[dict[str, Any]]:
    for node in nodes:
        schema = getattr(node, "form_schema", None)
        if isinstance(node, dict):
            schema = node.get("form_schema")
        forms = extract_form_library(schema)
        if forms:
            return forms
    return []


def strip_form_library(form_schema: Any) -> Any:
    if not isinstance(form_schema, dict):
        return deepcopy(form_schema)
    cloned = deepcopy(form_schema)
    cloned.pop(FORM_LIBRARY_KEY, None)
    return cloned if cloned else None


def inject_form_library(form_schema: Any, forms: list[dict[str, Any]] | None) -> Any:
    normalized_forms = normalize_form_library(forms)
    schema = strip_form_library(form_schema)
    if schema is None:
        schema = {}
    if not isinstance(schema, dict):
        schema = {}
    if normalized_forms:
        schema[FORM_LIBRARY_KEY] = normalized_forms
    return schema if schema else None

