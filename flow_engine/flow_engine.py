import json
import logging
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from flow_engine.models import FlowInstance, FlowLog, FlowTask
from flow_engine.utils.flow_engine_util import SafeEvaluator

logger = logging.getLogger(__name__)


class FlowEngine:
    """通用工作流引擎（Django权限控制版）"""

    def __init__(self, instance: FlowInstance):
        self.instance = instance
        self.flow = instance.flow
        logger.debug(f"[FlowEngine] 初始化流程实例 id={instance.id}, flow={self.flow.name}")

    # ----------------------------
    # 公共方法
    # ----------------------------
    def start(self, user=None):
        """启动流程"""
        start_node = self.flow.nodes.filter(node_type="start").first()
        if not start_node:
            raise Exception("流程未定义开始节点")

        if user and not self._check_node_permission(start_node, user):
            raise PermissionError(f"用户 {user} 无权启动流程 {self.flow.name}")

        self.instance.current_node = start_node
        self.instance.status = "running"
        self.instance.save()

        FlowLog.objects.create(instance=self.instance, node=start_node, user=user, action="start", message="流程启动")
        logger.info(f"[FlowEngine] 流程启动 id={self.instance.id}, 起点={start_node.name}, user={user}")
        self._enter_node(start_node)

    @transaction.atomic
    def approve(self, user, comment=None, context=None):
        """审批通过"""
        node = self.instance.current_node
        self._check_node_permission(node, user)

        task = FlowTask.objects.filter(
            instance=self.instance, node=node, assignee=user, status="pending"
        ).first()
        if not task:
            raise Exception("无可处理任务或非当前节点处理人")

        task.status = "approved"
        task.comment = comment
        task.save()
        FlowLog.objects.create(instance=self.instance, node=node, user=user, action="approve", message=comment)

        logger.info(f"[FlowEngine] 审批通过 user={user}, node={node.name}, comment={comment}")
        self._exit_node(node)
        self._go_next(context or {})

    @transaction.atomic
    def reject(self, user, comment=None):
        """审批驳回到上一步"""
        node = self.instance.current_node
        self._check_node_permission(node, user)

        task = FlowTask.objects.filter(
            instance=self.instance, node=node, assignee=user, status="pending"
        ).first()
        if not task:
            raise Exception("无可处理任务或非当前节点处理人")

        task.status = "rejected"
        task.comment = comment
        task.save()

        FlowLog.objects.create(instance=self.instance, node=node, user=user, action="reject", message=comment)
        self.instance.status = "rejected"
        self.instance.save()
        logger.warning(f"[FlowEngine] 审批驳回 user={user}, node={node.name}, comment={comment}")

    def next(self, user=None, context=None):
        """直接推进节点（自动节点或条件节点用）"""
        node = self.instance.current_node
        if user:
            self._check_node_permission(node, user)
        logger.info(f"[FlowEngine] 手动推进流程 id={self.instance.id}, node={node.name}, user={user}")
        self._go_next(context or {})

    # ----------------------------
    # 权限校验
    # ----------------------------
    def _check_permission(self, user):
        """检查当前用户是否有权限操作当前节点"""
        node = self.instance.current_node

        # 超级用户永远放行
        if user.is_superuser:
            return True

        # 没有权限限制的节点默认放行
        node_perms = node.permissions.all()
        if not node_perms.exists():
            return True

        user_perms = user.get_all_permissions()
        for p in node_perms:
            full_code = f"{p.content_type.app_label}.{p.codename}"
            if full_code in user_perms:
                return True

        raise PermissionDenied(f"用户[{user}]无权操作节点[{node.name}]")

    # ----------------------------
    # 内部流程逻辑
    # ----------------------------
    def _go_next(self, context):
        """推进到下一个节点"""
        current = self.instance.current_node
        next_node = self._get_next_node(current, context)
        logger.debug(f"[FlowEngine] 当前节点={current.name}, 下一个节点={getattr(next_node, 'name', None)}")

        if not next_node:
            self.instance.status = "finished"
            self.instance.save()
            FlowLog.objects.create(instance=self.instance, node=current, action="finish", message="流程结束")
            logger.info(f"[FlowEngine] 流程结束 id={self.instance.id}")
            return

        self.instance.current_node = next_node
        self.instance.save()
        FlowLog.objects.create(instance=self.instance, node=next_node, action="enter", message=f"进入节点：{next_node.name}")
        logger.info(f"[FlowEngine] 进入下一个节点 id={self.instance.id}, node={next_node.name}")
        self._enter_node(next_node)

    def _get_next_node(self, node, context):
        """解析下一个节点"""
        transitions = node.source_transitions.all()
        if node.node_type == "condition":
            logger.debug(f"[FlowEngine] 条件节点解析: {node.name}, context={context}")
            for t in transitions:
                if not t.condition_expr:
                    continue
                try:
                    expr = json.loads(t.condition_expr)
                    evaluator = SafeEvaluator(context)
                    if evaluator.eval_expr(expr):
                        logger.debug(f"[FlowEngine] 条件命中: {t.condition_expr} → {t.target.name}")
                        return t.target
                except Exception as e:
                    logger.exception(f"[FlowEngine] 条件解析错误 node={node.name}: {e}")

            default_t = transitions.filter(condition_expr__isnull=True).first()
            if default_t:
                logger.debug(f"[FlowEngine] 条件未命中，使用默认分支 → {default_t.target.name}")
                return default_t.target
            return None

        t = transitions.filter(condition_expr__isnull=True).first()
        return t.target if t else None

    def _enter_node(self, node):
        """节点进入事件"""
        logger.debug(f"[FlowEngine] 进入节点: {node.name} ({node.node_type})")
        if node.node_type == "task":
            FlowTask.objects.create(instance=self.instance, node=node, assignee=self._find_assignee(node))
            logger.info(f"[FlowEngine] 创建任务 node={node.name}")
        elif node.node_type == "condition":
            self._go_next({})
        elif node.node_type == "end":
            self.instance.status = "finished"
            self.instance.save()
            logger.info(f"[FlowEngine] 流程结束节点触发 id={self.instance.id}")

    def _exit_node(self, node):
        """节点退出事件"""
        FlowTask.objects.filter(instance=self.instance, node=node, status="pending").update(status="done")
        logger.debug(f"[FlowEngine] 节点退出: {node.name}")

    def _find_assignee(self, node):
        """根据权限分配处理人"""
        User = get_user_model()
        if node.role:
            users = [u for u in User.objects.all() if u.has_perm(node.role)]
            if users:
                assignee = users[0]
                logger.debug(f"[FlowEngine] 节点 {node.name} 分配给具有权限 {node.role} 的用户 {assignee}")
                return assignee
        assignee = User.objects.filter(is_superuser=True).first()
        logger.debug(f"[FlowEngine] 节点 {node.name} 未找到匹配权限用户，默认分配 {assignee}")
        return assignee
