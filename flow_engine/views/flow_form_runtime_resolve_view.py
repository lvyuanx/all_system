# -*-coding:utf-8 -*-

"""
# Description: resolve runtime form schema/data by instance context
"""

from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Body
from flow_engine.models import FlowInstance, FlowTask
from flow_engine.utils.form_runtime_util import resolve_form_runtime

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "resolve flow runtime form failed"
    response_schema = schemas.FlowFormRuntimeResolveRespSchema
    error_codes = [
        ("001", "flow instance not found"),
        ("002", "current user has no pending task on this node"),
        ("003", "current node not found"),
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
    async def api(
        request: HttpRequest,
        data: schemas.FlowFormRuntimeResolveSchema = Body(..., description="resolve runtime form"),
    ):
        def _query_instance():
            return (
                FlowInstance.objects.select_related("current_node")
                .filter(id=data.instance_id)
                .first()
            )

        instance = await sync_to_async(_query_instance, thread_sensitive=True)()
        if not instance:
            raise BusinessException("001")

        node = instance.current_node
        if data.task_id:
            def _query_task_node():
                task = (
                    FlowTask.objects.select_related("node")
                    .filter(
                        id=data.task_id,
                        instance_id=instance.id,
                        status="pending",
                    )
                    .first()
                )
                return task

            task = await sync_to_async(_query_task_node, thread_sensitive=True)()
            if not task:
                raise BusinessException("002")
            if (not request.user.is_superuser) and task.assignee_id != request.user.id:
                raise BusinessException("002")
            node = task.node
        else:
            if not request.user.is_superuser:
                has_task = await sync_to_async(
                    lambda: FlowTask.objects.filter(
                        instance_id=instance.id,
                        node_id=getattr(node, "id", None),
                        assignee=request.user,
                        status="pending",
                    ).exists(),
                    thread_sensitive=True,
                )()
                if not has_task:
                    raise BusinessException("002")

        if not node:
            raise BusinessException("003")

        raw_schema = View._strip_form_schema_ui(getattr(node, "form_schema", None))
        resolved_schema, resolved_form_data = await sync_to_async(
            lambda: resolve_form_runtime(
                form_schema=raw_schema,
                context=instance.context or {},
                node_code=node.code or "",
                runtime_env={
                    "business_type": instance.business_type,
                    "business_id": instance.business_id,
                },
            ),
            thread_sensitive=True,
        )()

        return schemas.FlowFormRuntimeResolveRespSchema(
            instance_id=instance.id,
            node_code=node.code or "",
            node_name=node.name or "",
            resolved_form_schema=resolved_schema or {},
            resolved_form_data=resolved_form_data or {},
            context_snapshot=instance.context or {},
        )
