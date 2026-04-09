# -*- coding: utf-8 -*-
import csv
from typing import List, Dict, Optional

def read_csv_as_dicts(csv_file: str, encoding: str = "utf-8-sig", skip_fields: Optional[List[str]] = None) -> List[Dict]:
    """
    读取 CSV 文件，返回字典列表，可选择跳过指定字段。
    
    参数:
        csv_file: CSV 文件路径
        encoding: 文件编码，默认 utf-8
        skip_fields: 可选列表，指定要跳过的字段
    
    返回:
        List[Dict]，每一行数据对应一个字典
    """
    skip_fields = skip_fields or []
    result = []

    with open(csv_file, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_dict = {k: v.strip() for k, v in row.items() if k not in skip_fields}
            result.append(row_dict)

    return result
