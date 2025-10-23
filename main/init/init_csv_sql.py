# -*-coding:utf-8 -*-

"""
# File       : init_menus.py
# Time       : 2025-10-15 23:26:50
# Author     : lyx
# version    : python 3.11
# Description: 初始化菜单
"""
import logging

from django.apps import apps
from django.conf import settings
from django.db.models import Q

from core.utils import db_util, module_util

logger = logging.getLogger(__name__)
db_csvs = settings.DB_CSVS


def init_csv_sql():
    if not db_csvs:
        logger.warning("未配置数据库初始化文件")
        return
    
    for csv_path, model_path, unique_fields, skip_fields in db_csvs:
        logger.info(f"初始化数据库文件：{csv_path} ...")
        model_class = apps.get_model(model_path)
        
        # 读取 CSV 数据，跳过 id
        model_datas = db_util.read_csv_as_dicts(csv_path, skip_fields=skip_fields)
        if not model_datas:
            continue

        # 构建联合唯一判断的查询 Q 对象
        q_objects = Q()
        for data in model_datas:
            q = Q()
            for field in unique_fields:
                if field in data:
                    q &= Q(**{field: data[field]})
            q_objects |= q  # 把每一条记录的联合条件用 OR 连接
        # 查询已存在的记录
        existing_records = model_class.objects.filter(q_objects).values_list(*unique_fields)
        existing_records_join = []
        for record in existing_records:
            existing_records_join.append(
                "|".join([str(item) for item in record])
            )
        existing_records_set = set(existing_records_join)

        # 构建待创建对象列表，跳过已存在的记录
        to_create = []
        for data in model_datas:
            key = tuple(data[field] for field in unique_fields if field in data)
            if "|".join([str(item) for item in key]) not in existing_records_set:
                to_create.append(model_class(**data))

        # 批量创建
        if to_create:
            model_class.objects.bulk_create(to_create)

        logger.info(f"共插入 {len(to_create)} 条数据，跳过 {len(model_datas) - len(to_create)} 条已存在数据。")

