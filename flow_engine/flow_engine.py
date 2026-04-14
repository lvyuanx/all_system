import json
import hashlib
import logging
from typing import Iterable

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

from flow_engine.enums import (
    NodeTypeChoices,
    FlowStatusChoices,
    TaskStatusChoices,
    ApprovalModeChoices,
    RuleTypeChoices,
    FlowVersionStatusChoices,
    FlowMigrationStatusChoices,
)
from flow_engine.models import (
    FlowDefinition,
    FlowVersion,
    FlowNodeVersion,
    FlowTransitionVersion,
    FlowNodeGroup,
    FlowNodeGroupRule,
    FlowInstance,
    FlowTask,
    FlowLog,
    FlowMigrationPlan,
    FlowMigrationJob,
)
from flow_engine.utils.flow_engine_util import SafeEvaluator
from flow_engine.utils.form_runtime_util import deep_merge_dict
from flow_engine.signals import flow_instance_finished_signal

logger = logging.getLogger(__name__)
User = get_user_model()


class FlowEngineError(Exception):
    pass


class FlowEngine:
    """Workflow engine with version snapshots and group-based permissions."""

    def __init__(self, instance: FlowInstance):
        self.instance = instance
        self.flow = instance.flow
        self.version = instance.flow_version
        logger.debug(
            "[FlowEngine] init instance=%s flow=%s version=%s",
            instance.id,
            getattr(self.flow, "name", None),
            getattr(self.version, "version_label", None),
        )

    # -------------------------------------------------------------
    # Publish & Start helpers
    # -------------------------------------------------------------
    @classmethod
    def publish_definition(cls, flow_def: FlowDefinition, published_by=None) -> FlowVersion:
        """Publish a new version snapshot from a definition."""
        if not flow_def:
            raise FlowEngineError("Flow definition is required.")
        if not flow_def.nodes.exists():
            raise FlowEngineError("Flow definition has no nodes.")
        if not flow_def.nodes.filter(node_type=NodeTypeChoices.START).exists():
            raise FlowEngineError("Flow definition has no start node.")

        with transaction.atomic():
            FlowVersion.objects.filter(
                definition=flow_def, status=FlowVersionStatusChoices.PUBLISHED
            ).update(status=FlowVersionStatusChoices.RETIRED, retired_at=timezone.now())

            latest = (
                FlowVersion.objects.filter(definition=flow_def)
                .aggregate(max_no=Max("version_no"))
                .get("max_no")
                or 0
            )
            version_no = latest + 1
            version = FlowVersion.objects.create(
                definition=flow_def,
                version_no=version_no,
                status=FlowVersionStatusChoices.PUBLISHED,
                published_at=timezone.now(),
                published_by=published_by,
            )
            flow_def.version = version.version_label
            flow_def.save(update_fields=["version"])

            # copy nodes
            node_map: dict[int, FlowNodeVersion] = {}
            for node in flow_def.nodes.all().order_by("order", "id"):
                v_node = FlowNodeVersion.objects.create(
                    flow_version=version,
                    code=node.code,
                    name=node.name,
                    node_type=node.node_type,
                    approval_mode=getattr(node, "approval_mode", ApprovalModeChoices.ANY),
                    form_schema=node.form_schema,
                    is_auto=node.is_auto,
                    order=node.order,
                )
                if node.permissions.exists():
                    v_node.permissions.set(node.permissions.all())
                node_map[node.id] = v_node

                # copy groups and rules
                for group in node.groups.all().order_by("order", "id"):
                    v_group = FlowNodeGroup.objects.create(
                        node_version=v_node,
                        key=group.key,
                        name=group.name,
                        min_approve_count=group.min_approve_count,
                        order=group.order,
                    )
                    for rule in group.rules.all():
                        FlowNodeGroupRule.objects.create(
                            group=v_group,
                            rule_type=rule.rule_type,
                            perm_pack=rule.perm_pack,
                            user=rule.user,
                        )

            # copy transitions
            for trans in flow_def.transitions.all().order_by("id"):
                FlowTransitionVersion.objects.create(
                    flow_version=version,
                    source=node_map.get(trans.source_id),
                    target=node_map.get(trans.target_id),
                    condition_expr=trans.condition_expr,
                    description=trans.description,
                )

            snapshot = cls._build_snapshot(version)
            snapshot_str = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
            version.snapshot_json = snapshot
            version.snapshot_hash = hashlib.sha256(snapshot_str.encode("utf-8")).hexdigest()
            version.save(update_fields=["snapshot_json", "snapshot_hash"])

            logger.info(
                "[FlowEngine] published flow=%s version=%s",
                flow_def.code,
                version.version_label,
            )
            return version

    @classmethod
    def start_for_business(
        cls,
        flow_def: FlowDefinition,
        business_type: str,
        business_id: str,
        creator=None,
        context: dict | None = None,
        version: FlowVersion | None = None,
    ) -> FlowInstance:
        """Create and start a flow instance for a business object."""
        if not flow_def:
            raise FlowEngineError("Flow definition is required.")
        if not flow_def.is_active:
            raise FlowEngineError("Flow definition is inactive.")

        flow_version = version or cls.get_latest_published_version(flow_def)
        if not flow_version:
            raise FlowEngineError("No published version found.")

        with transaction.atomic():
            existing = FlowInstance.objects.filter(
                business_type=business_type, business_id=business_id
            ).first()
            if existing:
                if not existing.current_node_id:
                    cls(existing).start(user=creator, context=context or {})
                return existing
            instance = FlowInstance.objects.create(
                flow=flow_def,
                flow_version=flow_version,
                business_type=business_type,
                business_id=business_id,
                creator=creator,
                context=context or {},
            )
            engine = cls(instance)
            engine.start(user=creator, context=context or {})
            return instance

    @classmethod
    def get_latest_published_version(cls, flow_def: FlowDefinition) -> FlowVersion | None:
        return (
            FlowVersion.objects.filter(
                definition=flow_def, status=FlowVersionStatusChoices.PUBLISHED
            )
            .order_by("-version_no", "-published_at")
            .first()
        )

    # -------------------------------------------------------------
    # Instance lifecycle
    # -------------------------------------------------------------
    def start(self, user=None, context: dict | None = None):
        if self.instance.current_node_id:
            return

        start_node = FlowNodeVersion.objects.filter(
            flow_version=self.version, node_type=NodeTypeChoices.START
        ).order_by("order", "id").first()
        if not start_node:
            raise FlowEngineError("Start node not found.")

        if user and not self._check_node_permission(start_node, user):
            raise PermissionDenied("User has no permission to start this flow.")

        self.instance.current_node = start_node
        self.instance.status = FlowStatusChoices.RUNNING
        if context:
            self.instance.context = deep_merge_dict(self.instance.context or {}, context)
        self.instance.save()

        flow_name = str(getattr(self.instance.flow, "name", "") or "").strip()
        start_message = f"流程已启动：{flow_name}" if flow_name else "流程已启动"
        FlowLog.objects.create(
            instance=self.instance,
            node=start_node,
            user=user,
            action="start",
            message=start_message,
        )

        self._enter_node(start_node, context or {})

    @transaction.atomic
    def approve(self, user, comment: str | None = None, context: dict | None = None, task_id: int | None = None):
        node = self.instance.current_node
        if not node:
            raise FlowEngineError("No current node.")

        self._check_node_permission(node, user)

        task_qs = FlowTask.objects.filter(
            instance=self.instance,
            node=node,
            assignee=user,
            status=TaskStatusChoices.PENDING,
        )
        if task_id:
            task_qs = task_qs.filter(id=task_id)

        tasks = list(task_qs)
        if not tasks and user.is_superuser:
            task_qs = FlowTask.objects.filter(
                instance=self.instance,
                node=node,
                status=TaskStatusChoices.PENDING,
            )
            if task_id:
                task_qs = task_qs.filter(id=task_id)
            tasks = list(task_qs)
        if not tasks:
            raise FlowEngineError("No pending task for current node.")
        if len(tasks) > 1 and not task_id:
            raise FlowEngineError("Multiple tasks found, task_id is required.")

        task = tasks[0]
        task.status = TaskStatusChoices.APPROVED
        task.comment = comment
        task.finish_time = timezone.now()
        task.save(update_fields=["status", "comment", "finish_time"])

        FlowLog.objects.create(
            instance=self.instance,
            node=node,
            user=user,
            action="approve",
            message=comment,
        )

        if self._is_node_complete(node):
            self._exit_node(node)
            self._go_next(context or {})

    @transaction.atomic
    def reject(self, user, comment: str | None = None, task_id: int | None = None):
        node = self.instance.current_node
        if not node:
            raise FlowEngineError("No current node.")

        # 检查当前节点是否是开始节点，开始节点无法驳回
        if node.node_type == NodeTypeChoices.START:
            raise FlowEngineError("开始节点无法驳回。")

        self._check_node_permission(node, user)

        task_qs = FlowTask.objects.filter(
            instance=self.instance,
            node=node,
            assignee=user,
            status=TaskStatusChoices.PENDING,
        )
        if task_id:
            task_qs = task_qs.filter(id=task_id)

        tasks = list(task_qs)
        if not tasks and user.is_superuser:
            task_qs = FlowTask.objects.filter(
                instance=self.instance,
                node=node,
                status=TaskStatusChoices.PENDING,
            )
            if task_id:
                task_qs = task_qs.filter(id=task_id)
            tasks = list(task_qs)
        if not tasks:
            raise FlowEngineError("No pending task for current node.")
        if len(tasks) > 1 and not task_id:
            raise FlowEngineError("Multiple tasks found, task_id is required.")

        task = tasks[0]
        task.status = TaskStatusChoices.REJECTED
        task.comment = comment
        task.finish_time = timezone.now()
        task.save(update_fields=["status", "comment", "finish_time"])

        # 取消当前节点的其他待处理任务
        FlowTask.objects.filter(
            instance=self.instance,
            node=node,
            status=TaskStatusChoices.PENDING,
        ).exclude(id=task.id).update(
            status=TaskStatusChoices.CANCELED,
            finish_time=timezone.now(),
        )

        if self.instance.status != FlowStatusChoices.RUNNING:
            self.instance.status = FlowStatusChoices.RUNNING
            self.instance.save(update_fields=["status"])

        # 找到驳回的目标节点
        target_node = self._find_reject_target_node(node)
        if not target_node:
            raise FlowEngineError("无法找到可驳回的目标节点。")

        # 退出当前节点
        self._exit_node(node)

        # 进入目标节点
        self.instance.current_node = target_node
        self.instance.save(update_fields=["current_node"])

        # 记录驳回日志
        reject_msg = f"驳回至 {target_node.name}"
        if comment:
            reject_msg += f"：{comment}"
        FlowLog.objects.create(
            instance=self.instance,
            node=node,
            user=user,
            action="reject",
            message=reject_msg,
        )

        self._enter_node(target_node, self.instance.context or {})

    def _get_node_history(self) -> list[FlowNodeVersion]:
        """
        从流程日志中获取节点访问历史，按时间顺序排列（最早的在前）
        """
        logs = FlowLog.objects.filter(
            instance=self.instance,
            action="enter"
        ).order_by("create_time")

        history = []
        seen_node_ids = set()
        for log in logs:
            if log.node_id and log.node_id not in seen_node_ids:
                history.append(log.node)
                seen_node_ids.add(log.node_id)
        return history

    def _find_reject_target_node(self, current_node: FlowNodeVersion) -> FlowNodeVersion | None:
        """
        找到驳回的目标节点：
        1. 返回上一个节点
        2. 如果上一个节点是自动节点，继续找上上节点，直到找到开始节点或非自动节点
        3. 如果开始节点也是自动节点，则找第一个任务节点
        """
        history = self._get_node_history()

        # 找到当前节点在历史中的位置
        try:
            current_idx = history.index(current_node)
        except ValueError:
            # 如果当前节点不在历史中，使用最后一个位置
            current_idx = len(history)

        # 从当前节点的前一个节点开始往前找
        for i in range(current_idx - 1, -1, -1):
            node = history[i]

            # 如果是开始节点，检查是否可以驳回
            if node.node_type == NodeTypeChoices.START:
                # 如果开始节点不是自动节点，可以驳回到此
                if not node.is_auto:
                    return node
                # 如果开始节点是自动节点，继续找第一个任务节点
                continue

            # 如果是非自动的任务节点，可以驳回到此
            if not node.is_auto and node.node_type == NodeTypeChoices.TASK:
                return node

        # 如果历史中没有找到合适的节点，直接在流程图中找第一个任务节点
        return self._find_first_task_node()

    def _find_first_task_node(self) -> FlowNodeVersion | None:
        """
        找到流程中第一个非自动的任务节点
        """
        # 先按顺序查找非自动的任务节点
        nodes = FlowNodeVersion.objects.filter(
            flow_version=self.version,
            node_type=NodeTypeChoices.TASK,
            is_auto=False
        ).order_by("order", "id")

        first_task = nodes.first()
        if first_task:
            return first_task

        # 如果没有非自动的任务节点，找任意任务节点
        nodes = FlowNodeVersion.objects.filter(
            flow_version=self.version,
            node_type=NodeTypeChoices.TASK
        ).order_by("order", "id")

        return nodes.first()

    def next(self, user=None, context: dict | None = None):
        node = self.instance.current_node
        if not node:
            raise FlowEngineError("No current node.")
        if user:
            self._check_node_permission(node, user)
        self._go_next(context or {})

    # -------------------------------------------------------------
    # Migration
    # -------------------------------------------------------------
    @classmethod
    def migrate_instance(
        cls,
        plan: FlowMigrationPlan,
        instance: FlowInstance,
        operator=None,
    ) -> FlowMigrationJob:
        job = FlowMigrationJob.objects.create(
            plan=plan,
            instance=instance,
            status=FlowMigrationStatusChoices.RUNNING,
        )

        try:
            if instance.flow_version_id != plan.from_version_id:
                raise FlowEngineError("Instance version does not match migration plan.")
            if plan.definition_id != instance.flow_id:
                raise FlowEngineError("Migration plan does not match flow definition.")

            rule_json = plan.rule_json or {}
            node_map = {
                item.get("from"): item.get("to")
                for item in rule_json.get("node_map", [])
                if item.get("from") and item.get("to")
            }
            task_policy = rule_json.get("task_policy", "cancel_and_recreate")

            target_version = plan.to_version
            target_node = None
            if instance.current_node:
                from_code = instance.current_node.code
                to_code = node_map.get(from_code, from_code)
                target_node = FlowNodeVersion.objects.filter(
                    flow_version=target_version, code=to_code
                ).first()
            if not target_node:
                target_node = FlowNodeVersion.objects.filter(
                    flow_version=target_version, node_type=NodeTypeChoices.START
                ).order_by("order", "id").first()

            if not target_node:
                raise FlowEngineError("Target node not found in new version.")

            # handle tasks
            if task_policy == "finish_then_migrate":
                if FlowTask.objects.filter(
                    instance=instance, status=TaskStatusChoices.PENDING
                ).exists():
                    raise FlowEngineError("Pending tasks exist, cannot migrate now.")

            if task_policy == "cancel_and_recreate":
                FlowTask.objects.filter(
                    instance=instance, status=TaskStatusChoices.PENDING
                ).update(status=TaskStatusChoices.CANCELED, finish_time=timezone.now())
            elif task_policy == "keep_and_continue":
                pending_tasks = FlowTask.objects.filter(
                    instance=instance, status=TaskStatusChoices.PENDING
                ).select_related("node")
                for task in pending_tasks:
                    from_code = task.node.code if task.node else None
                    to_code = node_map.get(from_code, from_code)
                    if not to_code:
                        continue
                    new_node = FlowNodeVersion.objects.filter(
                        flow_version=target_version, code=to_code
                    ).first()
                    if new_node and new_node.id != task.node_id:
                        task.node = new_node
                        task.save(update_fields=["node"])

            # update context by form_map if provided
            form_map = rule_json.get("form_map", [])
            if form_map and isinstance(instance.context, dict):
                instance.context = cls._apply_form_map(instance.context, form_map)

            instance.flow_version = target_version
            instance.current_node = target_node
            instance.save(update_fields=["flow_version", "current_node", "context"])

            FlowLog.objects.create(
                instance=instance,
                node=target_node,
                user=operator,
                action="migrate",
                message=f"migrate to {target_version.version_label}",
            )

            if task_policy == "cancel_and_recreate":
                cls(instance)._enter_node(target_node, {})

            job.status = FlowMigrationStatusChoices.SUCCESS
            job.result_json = {"to_version": target_version.version_label}
            job.finish_time = timezone.now()
            job.save(update_fields=["status", "result_json", "finish_time"])
            return job
        except Exception as exc:
            job.status = FlowMigrationStatusChoices.FAILED
            job.result_json = {"error": str(exc)}
            job.finish_time = timezone.now()
            job.save(update_fields=["status", "result_json", "finish_time"])
            raise

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------
    def _mark_instance_finished(self, node: FlowNodeVersion | None):
        self.instance.status = FlowStatusChoices.FINISHED
        self.instance.save(update_fields=["status"])
        FlowLog.objects.create(
            instance=self.instance,
            node=node,
            action="finish",
            message="流程已完成",
        )
        flow_instance_finished_signal.send(
            sender=FlowInstance,
            instance=self.instance,
        )

    def _go_next(self, context: dict):
        if context:
            self.instance.context = deep_merge_dict(self.instance.context or {}, context)
            self.instance.save(update_fields=["context"])
        merged_context = self.instance.context or {}
        current = self.instance.current_node
        next_node = self._get_next_node(current, merged_context)

        if not next_node:
            self._mark_instance_finished(current)
            return

        self.instance.current_node = next_node
        self.instance.save(update_fields=["current_node"])
        FlowLog.objects.create(
            instance=self.instance,
            node=next_node,
            action="enter",
            message=f"进入节点：{next_node.name}",
        )
        self._enter_node(next_node, merged_context)

    def _get_next_node(self, node: FlowNodeVersion, context: dict):
        transitions = node.outgoing_transitions.all()

        if node.node_type == NodeTypeChoices.CONDITION:
            for t in transitions:
                if not t.condition_expr:
                    continue
                try:
                    expr = json.loads(t.condition_expr)
                    evaluator = SafeEvaluator(context)
                    if evaluator.eval_expr(expr):
                        return t.target
                except Exception as exc:
                    logger.exception("condition eval error: %s", exc)

            default_t = transitions.filter(
                Q(condition_expr__isnull=True) | Q(condition_expr="")
            ).first()
            return default_t.target if default_t else None

        default_t = transitions.filter(
            Q(condition_expr__isnull=True) | Q(condition_expr="")
        ).first()
        return default_t.target if default_t else None

    def _enter_node(self, node: FlowNodeVersion, context: dict):
        if node.node_type in (NodeTypeChoices.START, NodeTypeChoices.CONDITION):
            self._go_next(context)
            return
        if node.node_type == NodeTypeChoices.END:
            self._mark_instance_finished(node)
            return

        if node.is_auto:
            self._go_next(context)
            return

        self._create_tasks(node)

    def _exit_node(self, node: FlowNodeVersion):
        FlowTask.objects.filter(
            instance=self.instance,
            node=node,
            status=TaskStatusChoices.PENDING,
        ).update(status=TaskStatusChoices.CANCELED, finish_time=timezone.now())

    def _create_tasks(self, node: FlowNodeVersion):
        groups = list(node.groups.all().order_by("order", "id"))
        created = 0

        if groups:
            for group in groups:
                candidate_ids = self._get_group_candidates(group)
                if len(candidate_ids) < max(group.min_approve_count, 1):
                    logger.warning(
                        "node=%s group=%s candidates=%s < min_approve_count=%s",
                        node.id,
                        group.key,
                        len(candidate_ids),
                        group.min_approve_count,
                    )
                for uid in candidate_ids:
                    if FlowTask.objects.filter(
                        instance=self.instance,
                        node=node,
                        assignee_id=uid,
                        group_key=group.key,
                        status=TaskStatusChoices.PENDING,
                    ).exists():
                        continue
                    FlowTask.objects.create(
                        instance=self.instance,
                        node=node,
                        assignee_id=uid,
                        group_key=group.key,
                        status=TaskStatusChoices.PENDING,
                    )
                    created += 1
        else:
            candidate_ids = self._get_permission_candidates(node)
            if not candidate_ids:
                super_user = User.objects.filter(is_superuser=True).first()
                if super_user:
                    candidate_ids = [super_user.id]
            for uid in candidate_ids:
                if FlowTask.objects.filter(
                    instance=self.instance,
                    node=node,
                    assignee_id=uid,
                    status=TaskStatusChoices.PENDING,
                ).exists():
                    continue
                FlowTask.objects.create(
                    instance=self.instance,
                    node=node,
                    assignee_id=uid,
                    status=TaskStatusChoices.PENDING,
                )
                created += 1

        if created == 0:
            logger.warning("no tasks created for node=%s", node.id)

    def _check_node_permission(self, node: FlowNodeVersion, user) -> bool:
        if user.is_superuser:
            return True

        groups = list(node.groups.all())
        if groups:
            for group in groups:
                if user.id in self._get_group_candidates(group):
                    return True
            raise PermissionDenied("User has no permission for this node.")

        # fallback to permissions
        perms = node.permissions.all()
        if not perms.exists():
            return True
        user_perms = user.get_all_permissions()
        for p in perms:
            full_code = f"{p.content_type.app_label}.{p.codename}"
            if full_code in user_perms:
                return True
        raise PermissionDenied("User has no permission for this node.")

    def _get_group_candidates(self, group: FlowNodeGroup) -> list[int]:
        candidate_ids: set[int] = set()
        for rule in group.rules.all():
            if rule.rule_type == RuleTypeChoices.USER and rule.user_id:
                candidate_ids.add(rule.user_id)
            elif rule.rule_type == RuleTypeChoices.PERM_PACK and rule.perm_pack_id:
                pack_user_ids = (
                    User.objects.filter(groups__permission_packs=rule.perm_pack)
                    .values_list("id", flat=True)
                    .distinct()
                )
                candidate_ids.update(pack_user_ids)
        return list(candidate_ids)

    def _get_permission_candidates(self, node: FlowNodeVersion) -> list[int]:
        perms = node.permissions.all()
        if not perms.exists():
            return []
        candidates = User.objects.filter(
            Q(user_permissions__in=perms) | Q(groups__permissions__in=perms)
        ).values_list("id", flat=True)
        return list(set(candidates))

    def _is_node_complete(self, node: FlowNodeVersion) -> bool:
        groups = list(node.groups.all())
        if not groups:
            return FlowTask.objects.filter(
                instance=self.instance,
                node=node,
                status=TaskStatusChoices.APPROVED,
            ).exists()

        group_results: list[bool] = []
        for group in groups:
            approved_count = FlowTask.objects.filter(
                instance=self.instance,
                node=node,
                group_key=group.key,
                status=TaskStatusChoices.APPROVED,
            ).count()
            group_results.append(approved_count >= max(group.min_approve_count, 1))

        if node.approval_mode == ApprovalModeChoices.ALL:
            return all(group_results) if group_results else False
        return any(group_results) if group_results else False

    # -------------------------------------------------------------
    # Snapshot utilities
    # -------------------------------------------------------------
    @staticmethod
    def _build_snapshot(version: FlowVersion) -> dict:
        nodes = []
        for node in version.nodes.all().order_by("order", "id"):
            perm_codes = [
                f"{p.content_type.app_label}.{p.codename}" for p in node.permissions.all()
            ]
            groups = []
            for group in node.groups.all().order_by("order", "id"):
                rules = []
                for rule in group.rules.all():
                    if rule.rule_type == RuleTypeChoices.PERM_PACK and rule.perm_pack:
                        rules.append(
                            {
                                "type": "perm_pack",
                                "pack_code": rule.perm_pack.pack_code,
                                "pack_name": rule.perm_pack.pack_name,
                            }
                        )
                    elif rule.rule_type == RuleTypeChoices.USER and rule.user:
                        rules.append(
                            {
                                "type": "user",
                                "user_id": rule.user_id,
                                "user_name": getattr(rule.user, "full_name", None),
                            }
                        )
                groups.append(
                    {
                        "key": group.key,
                        "name": group.name,
                        "min_approve_count": group.min_approve_count,
                        "rules": rules,
                    }
                )

            nodes.append(
                {
                    "code": node.code,
                    "name": node.name,
                    "node_type": node.node_type,
                    "approval_mode": node.approval_mode,
                    "is_auto": node.is_auto,
                    "order": node.order,
                    "form_schema": node.form_schema,
                    "permissions": perm_codes,
                    "groups": groups,
                }
            )

        transitions = []
        for trans in version.transitions.all().order_by("id"):
            transitions.append(
                {
                    "from": trans.source.code,
                    "to": trans.target.code,
                    "condition_expr": trans.condition_expr,
                    "description": trans.description,
                }
            )

        return {
            "definition_code": version.definition.code,
            "definition_name": version.definition.name,
            "version_no": version.version_no,
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "nodes": nodes,
            "transitions": transitions,
        }

    @staticmethod
    def _apply_form_map(context: dict, form_map: Iterable[dict]) -> dict:
        def _get_path(data: dict, path: str):
            cur = data
            for part in path.split("."):
                if not isinstance(cur, dict):
                    return None
                cur = cur.get(part)
            return cur

        def _set_path(data: dict, path: str, value):
            cur = data
            parts = path.split(".")
            for part in parts[:-1]:
                if part not in cur or not isinstance(cur[part], dict):
                    cur[part] = {}
                cur = cur[part]
            cur[parts[-1]] = value

        new_context = dict(context)
        for item in form_map:
            src = item.get("from")
            dst = item.get("to")
            if not src or not dst:
                continue
            val = _get_path(new_context, src)
            if val is not None:
                _set_path(new_context, dst, val)
        return new_context
