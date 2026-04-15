# -*-coding:utf-8 -*-

"""
# File       : order_workflow_action_view.py
# Description: 订单流程审批动作
"""

import json
import posixpath
import re
import uuid
from pathlib import Path
from typing import Any

from asgiref.sync import sync_to_async
from core.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.models import Order
from site_mgmt.utils import site_util
from flow_engine.flow_engine import FlowEngine, FlowEngineError
from flow_engine.enums import FlowStatusChoices
from flow_engine.utils.form_library_util import FORM_REF_CODE_KEY, FORM_REF_NAME_KEY, resolve_form_ref_definition
from flow_engine.utils.form_runtime_util import build_context_updates_from_form_data

class View(BaseApi):
    FILE_UPLOAD_PREFIX = "wf_file__"
    SIGNATURE_UPLOAD_PREFIX = "wf_signature__"
    SIGNATURE_DATA_URL_RE = re.compile(
        r"^data:image/(?:png|jpeg|jpg|webp|gif);base64,[a-zA-Z0-9+/=\s]+$",
        re.IGNORECASE,
    )
    ALLOWED_SIGNATURE_TYPES = {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/gif",
    }

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "订单流程操作失败"
    response_schema = None
    error_codes = [
        ("001", "未查询到订单信息"),
        ("002", "当前订单未绑定运行中的流程"),
        ("003", "当前用户在该流程节点没有可操作任务"),
        ("004", "不支持的流程操作"),
        ("005", "请求参数格式错误"),
        ("006", "签名字段不支持 base64，请重新签名后提交"),
        ("007", "签名文件格式错误，仅支持图片"),
    ]

    @staticmethod
    def _strip_form_schema_ui(schema):
        if not isinstance(schema, dict):
            return schema
        cleaned = dict(schema)
        cleaned.pop("__ui", None)
        cleaned.pop("__form_library", None)
        return cleaned

    @staticmethod
    def _hydrate_form_schema(schema, node=None):
        if not isinstance(schema, dict):
            return schema
        ref_code = str(schema.get(FORM_REF_CODE_KEY) or "").strip()
        if not ref_code:
            return schema
        matched = resolve_form_ref_definition(ref_code, node)
        if not matched:
            return schema
        hydrated = {
            "fields": matched.get("fields") or [],
            FORM_REF_CODE_KEY: matched.get("code") or ref_code,
            FORM_REF_NAME_KEY: matched.get("name") or ref_code,
        }
        if "__ui" in schema:
            hydrated["__ui"] = schema["__ui"]
        return hydrated

    @staticmethod
    def _to_int(value, *, required: bool = False):
        if value in (None, ""):
            if required:
                raise BusinessException("005")
            return None
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            raise BusinessException("005")

    @staticmethod
    def _parse_json_form_data(raw_value) -> dict[str, Any]:
        if raw_value in (None, ""):
            return {}
        if isinstance(raw_value, dict):
            return raw_value
        if not isinstance(raw_value, str):
            raise BusinessException("005")
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            raise BusinessException("005")
        if decoded is None:
            return {}
        if not isinstance(decoded, dict):
            raise BusinessException("005")
        return decoded

    @staticmethod
    def _collect_uploads(request: HttpRequest, prefix: str) -> dict[str, list[UploadedFile]]:
        payload: dict[str, list[UploadedFile]] = {}
        for form_key, files in request.FILES.lists():
            if not form_key.startswith(prefix):
                continue
            field_key = str(form_key[len(prefix):] or "").strip()
            if not field_key:
                continue
            file_list = [item for item in files if item is not None]
            if not file_list:
                continue
            payload[field_key] = file_list
        return payload

    @staticmethod
    def _parse_request_payload(request: HttpRequest) -> dict[str, Any]:
        content_type = str(
            request.META.get("CONTENT_TYPE")
            or getattr(request, "content_type", "")
            or ""
        ).lower()
        is_json = "application/json" in content_type

        if is_json:
            try:
                raw_data = json.loads((request.body or b"{}").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise BusinessException("005")
            if not isinstance(raw_data, dict):
                raise BusinessException("005")
            order_id = View._to_int(raw_data.get("order_id"), required=True)
            task_id = View._to_int(raw_data.get("task_id"), required=False)
            action = str(raw_data.get("action") or "").strip().lower()
            operator_memo = raw_data.get("operator_memo")
            form_data = raw_data.get("form_data") or {}
            if form_data is None:
                form_data = {}
            if not isinstance(form_data, dict):
                raise BusinessException("005")
            file_uploads: dict[str, list[UploadedFile]] = {}
            signature_uploads: dict[str, list[UploadedFile]] = {}
        else:
            post_data = request.POST
            order_id = View._to_int(post_data.get("order_id"), required=True)
            task_id = View._to_int(post_data.get("task_id"), required=False)
            action = str(post_data.get("action") or "").strip().lower()
            operator_memo = post_data.get("operator_memo")
            form_data = View._parse_json_form_data(post_data.get("form_data"))
            file_uploads = View._collect_uploads(request, View.FILE_UPLOAD_PREFIX)
            signature_uploads = View._collect_uploads(request, View.SIGNATURE_UPLOAD_PREFIX)

        return {
            "order_id": order_id,
            "task_id": task_id,
            "action": action,
            "operator_memo": None if operator_memo is None else str(operator_memo),
            "form_data": form_data,
            "file_uploads": file_uploads,
            "signature_uploads": signature_uploads,
        }

    @staticmethod
    def _field_list(form_schema: Any) -> list[dict[str, Any]]:
        if isinstance(form_schema, list):
            return [item for item in form_schema if isinstance(item, dict)]
        if isinstance(form_schema, dict):
            fields = form_schema.get("fields")
            if isinstance(fields, list):
                return [item for item in fields if isinstance(item, dict)]
        return []

    @staticmethod
    def _iter_schema_fields(form_schema: Any) -> list[dict[str, Any]]:
        flat: list[dict[str, Any]] = []
        queue = list(View._field_list(form_schema))
        while queue:
            field = queue.pop(0)
            if not isinstance(field, dict):
                continue
            flat.append(field)
            for child_key in ("children", "fields", "items"):
                children = field.get(child_key)
                if isinstance(children, list):
                    queue.extend(item for item in children if isinstance(item, dict))
        return flat

    @staticmethod
    def _field_key(field: dict[str, Any]) -> str:
        return str(field.get("key") or field.get("name") or field.get("prop") or "").strip()

    @staticmethod
    def _field_component(field: dict[str, Any]) -> str:
        return str(field.get("component") or field.get("type") or "").strip().lower()

    @staticmethod
    def _is_signature_data_url(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        candidate = value.strip()
        if not candidate:
            return False
        return bool(View.SIGNATURE_DATA_URL_RE.match(candidate))

    @staticmethod
    def _is_allowed_signature_file(uploaded: UploadedFile) -> bool:
        content_type = str(getattr(uploaded, "content_type", "") or "").lower()
        if content_type in View.ALLOWED_SIGNATURE_TYPES:
            return True
        ext = Path(str(getattr(uploaded, "name", "") or "")).suffix.lower()
        return ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    @staticmethod
    def _build_media_url(relative_path: str) -> str:
        media_url = str(getattr(settings, "MEDIA_URL", "/media/") or "/media/")
        if not media_url.startswith("/"):
            media_url = f"/{media_url}"
        normalized_rel = str(relative_path or "").replace("\\", "/").lstrip("/")
        return f"{media_url.rstrip('/')}/{normalized_rel}"

    @staticmethod
    def _save_uploaded_file(uploaded: UploadedFile, *, flow_id: int, bucket: str) -> dict[str, Any]:
        original_name = str(getattr(uploaded, "name", "") or "").strip()
        ext = Path(original_name).suffix.lower()[:16]
        stored_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = posixpath.join("flow", str(flow_id), "form", bucket, stored_name)
        saved_relative_path = default_storage.save(relative_path, uploaded)
        normalized_saved_path = str(saved_relative_path).replace("\\", "/")
        return {
            "url": View._build_media_url(normalized_saved_path),
            "name": original_name or stored_name,
            "stored_name": posixpath.basename(normalized_saved_path),
            "size": int(getattr(uploaded, "size", 0) or 0),
        }

    @staticmethod
    def _apply_uploaded_form_assets(
        *,
        form_schema: Any,
        form_data: dict[str, Any],
        flow_id: int,
        file_uploads: dict[str, list[UploadedFile]],
        signature_uploads: dict[str, list[UploadedFile]],
    ) -> dict[str, Any]:
        payload = dict(form_data or {})
        schema_fields = View._iter_schema_fields(form_schema)
        field_map = {
            View._field_key(field): field
            for field in schema_fields
            if View._field_key(field)
        }

        for key, uploads in file_uploads.items():
            field = field_map.get(key)
            if not field:
                continue
            if View._field_component(field) != "file":
                continue
            valid_uploads = [item for item in uploads if item is not None]
            if not valid_uploads:
                continue
            metadata_list = [
                View._save_uploaded_file(item, flow_id=flow_id, bucket="upload")
                for item in valid_uploads
            ]
            if bool(field.get("multiple")):
                payload[key] = metadata_list
            else:
                payload[key] = metadata_list[0]

        for key, uploads in signature_uploads.items():
            field = field_map.get(key)
            if not field:
                continue
            if View._field_component(field) != "signature":
                continue
            valid_uploads = [item for item in uploads if item is not None]
            if not valid_uploads:
                continue
            signature_file = valid_uploads[-1]
            if not View._is_allowed_signature_file(signature_file):
                raise BusinessException("007")
            payload[key] = View._save_uploaded_file(
                signature_file,
                flow_id=flow_id,
                bucket="signature",
            )

        for field in schema_fields:
            if View._field_component(field) != "signature":
                continue
            key = View._field_key(field)
            if not key:
                continue
            if View._is_signature_data_url(payload.get(key)):
                raise BusinessException("006")

        return payload

    @staticmethod
    async def api(request: HttpRequest):
        payload = await sync_to_async(
            View._parse_request_payload,
            thread_sensitive=True,
        )(request)
        order_manager = Order.objects.filter(pk=payload["order_id"], is_delete=False)
        order_manager = await sync_to_async(site_util.admin_filter_site)(request, order_manager)
        if not await order_manager.aexists():
            raise BusinessException("001")

        order = await order_manager.select_related("flow_instance").afirst()
        if not order or not order.flow_instance_id:
            raise BusinessException("002")
        if order.flow_instance.status != FlowStatusChoices.RUNNING:
            raise BusinessException("002")

        def _do_action():
            engine = FlowEngine(order.flow_instance)
            if payload["action"] == "approve":
                current_node = order.flow_instance.current_node
                node_schema = View._hydrate_form_schema(
                    View._strip_form_schema_ui(getattr(current_node, "form_schema", None)),
                    current_node,
                )
                submit_form_data = View._apply_uploaded_form_assets(
                    form_schema=node_schema,
                    form_data=payload["form_data"] or {},
                    flow_id=int(order.flow_instance_id),
                    file_uploads=payload["file_uploads"] or {},
                    signature_uploads=payload["signature_uploads"] or {},
                )
                context_updates = build_context_updates_from_form_data(
                    form_schema=node_schema,
                    form_data=submit_form_data,
                    existing_context=order.flow_instance.context or {},
                    node_code=getattr(current_node, "code", "") or "",
                )
                engine.approve(
                    user=request.user,
                    comment=payload["operator_memo"],
                    context=context_updates,
                    task_id=payload["task_id"],
                )
                return
            if payload["action"] == "reject":
                engine.reject(
                    user=request.user,
                    comment=payload["operator_memo"],
                    task_id=payload["task_id"],
                )
                return
            raise BusinessException("004")

        try:
            await sync_to_async(_do_action, thread_sensitive=True)()
        except FlowEngineError:
            raise BusinessException("003")
