# -*-coding:utf-8 -*-
"""
# File       : flow_builder.py
# Time       : 2025-11-03 20:40:25
# Author     : lyx
# version    : python 3.11
# Description: 流程构建器，用于快速创建流程定义、节点、连线

# Example:
    builder = (
        FlowBuilder(name="订单生产流程", created_by="admin")
        .create_flow()
        .add_node("下单", NodeTypeChoices.START)
        .add_node("排班", NodeTypeChoices.TASK, permissions=["orders.can_schedule"])
        .add_node("生产", NodeTypeChoices.TASK, permissions=["orders.can_produce"])
        .add_node("配送", NodeTypeChoices.TASK, permissions=["orders.can_deliver"])
        .add_node("结束", NodeTypeChoices.END)
        .link_nodes("下单", "排班")
        .link_nodes("排班", "生产")
        .link_nodes("生产", "配送")
        .link_nodes("配送", "结束")
        .set_start("下单")
        .build()
    )

"""

import logging
from django.db import transaction
from django.contrib.auth.models import Permission
from flow_engine.models import FlowDefinition, FlowNode, FlowTransition

logger = logging.getLogger(__name__)


class FlowBuilder:
    """流程构建器：用于快速创建流程及节点定义"""

    def __init__(self, name: str, code: str = None, created_by="system"):
        self.name = name
        self.code = code or name.lower().replace(" ", "_")
        self.created_by = created_by
        self.flow = None
        self.node_map = {}

        logger.info(f"[FlowBuilder] 初始化: name={self.name}, code={self.code}, created_by={self.created_by}")

    # ----------------------------
    # 主流程构建方法
    # ----------------------------
    @transaction.atomic
    def create_flow(self):
        """创建流程定义"""
        logger.info(f"[FlowBuilder] 创建流程定义: {self.name} ({self.code})")
        self.flow = FlowDefinition.objects.create(
            name=self.name,
            code=self.code,
        )
        logger.debug(f"[FlowBuilder] ✅ FlowDefinition created id={self.flow.id}")
        return self

    def add_node(self, name: str, node_type: str, permissions=None, is_auto=False, order=None, code=None):
        """添加节点，可指定权限"""
        if not self.flow:
            raise ValueError("请先调用 create_flow() 创建流程定义")

        node = FlowNode.objects.create(
            flow=self.flow,
            code=code or name,
            name=name,
            node_type=node_type,
            is_auto=is_auto,
            order=order or len(self.node_map),
        )

        # 绑定权限（Permission queryset / list / str）
        if permissions:
            if isinstance(permissions, (list, tuple)):
                for p in permissions:
                    self._add_permission(node, p)
            else:
                self._add_permission(node, permissions)

        self.node_map[name] = node
        logger.debug(f"[FlowBuilder] 添加节点: {name} ({node_type}) id={node.id}")
        return self

    def link_nodes(self, from_name: str, to_name: str, condition_expr=None):
        """建立节点连线，可选条件表达式（JSON逻辑）"""
        if from_name not in self.node_map or to_name not in self.node_map:
            raise KeyError(f"无法连接节点：{from_name} → {to_name}，请确认已创建。")

        from_node = self.node_map[from_name]
        to_node = self.node_map[to_name]

        FlowTransition.objects.create(
            flow=self.flow,
            source=from_node,
            target=to_node,
            condition_expr=condition_expr or None,
        )
        logger.info(f"[FlowBuilder] 连接节点: {from_name} → {to_name} (条件={condition_expr})")
        return self

    def set_start(self, node_name: str):
        """设置起始节点"""
        if node_name not in self.node_map:
            raise KeyError(f"未找到节点：{node_name}")

        start_node = self.node_map[node_name]
        self.flow.nodes.filter(node_type="start").exclude(pk=start_node.pk).update(
            node_type="task"
        )
        start_node.node_type = "start"
        start_node.save(update_fields=["node_type"])
        logger.info(f"[FlowBuilder] 设置起点: {node_name}")
        return self

    def build(self):
        """构建完成"""
        total_nodes = len(self.node_map)
        logger.info(f"[FlowBuilder] ✅ 构建完成: {self.flow.name} (id={self.flow.id}), 节点数={total_nodes}")
        print(f"✅ 流程《{self.flow.name}》构建成功，共 {total_nodes} 个节点。")
        return self.flow

    # ----------------------------
    # 辅助函数
    # ----------------------------
    def _add_permission(self, node, perm):
        """为节点绑定权限，可接受 Permission 实例或字符串 codename"""
        if isinstance(perm, Permission):
            node.permissions.add(perm)
        elif isinstance(perm, str):
            try:
                app_label, codename = perm.split(".", 1)
                p = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                node.permissions.add(p)
            except Exception as e:
                logger.warning(f"[FlowBuilder] 权限 {perm} 未找到: {e}")
        else:
            logger.warning(f"[FlowBuilder] 无效权限类型: {type(perm)}")

