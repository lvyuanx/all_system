# -*-coding:utf-8 -*-

"""
# File       : base_admin.py
# Time       : 2025-09-08 11:09:05
# Author     : lyx
# version    : python 3.11
# Description: admin 基类
"""
class AdminBaseMixin:
    """通用 ModelAdmin 配置"""

    # 分页
    list_per_page = 10
    list_max_show_all = 200

    # 列表
    empty_value_display = ""   # 空值显示
    ordering = ("-id",)        # 默认按 id 倒序



    # 动作 & 按钮
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    save_as = False   # 编辑时允许“另存为”新对象
