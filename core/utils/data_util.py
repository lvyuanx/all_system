from datetime import datetime
from pydantic import BaseModel
from pydantic_core import PydanticUndefined
from typing import Any, Type, List, Union, get_args, get_origin
from core.utils import time_util


def generate_example(schema: Any) -> Any:
    """
    根据类型或模型自动生成示例数据，支持：
    - BaseModel 子类
    - List[BaseModel] 或 List[基础类型]
    - 基础类型（int、str、float、bool）
    - None
    """
    if schema is None:
        return None

    origin = get_origin(schema)
    args = get_args(schema)

    # 基础类型
    if schema in [str, int, float, bool]:
        return generate_value_by_type(schema)

    # 容器类型（如 List[str]、List[BaseModel]）
    if origin in [list, List]:
        item_type = args[0] if args else Any
        return [generate_example(item_type)]

    # 单个 BaseModel 实例或类
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return generate_example_for_model(schema)

    if isinstance(schema, BaseModel):
        return generate_example_for_model(schema.__class__)

    # 兜底（未知类型）
    return None


def generate_example_for_model(schema: Type[BaseModel]) -> dict:
    """
    根据 Pydantic 模型类生成示例数据。
    """
    example = {}

    for field_name, field_info in schema.model_fields.items():
        field_type = field_info.annotation
        default = field_info.default

        if default is not PydanticUndefined:
            example[field_name] = default
        else:
            example[field_name] = generate_value_by_type(field_type)

    return example


def generate_value_by_type(field_type: Any) -> Any:
    """
    根据字段类型生成示例值（基础类型、嵌套模型、集合类型等）。
    """
    origin = get_origin(field_type)
    args = get_args(field_type)

    if field_type in [str, int, float, bool]:
        return {
            str: "string",
            int: 0,
            float: 0.0,
            bool: True,
        }[field_type]

    if origin is dict:
        key_type, value_type = args or (str, Any)
        return {
            generate_value_by_type(key_type): generate_value_by_type(value_type)
        }

    if origin in [list, set, tuple]:
        value_type = args[0] if args else Any
        return [generate_value_by_type(value_type)]

    if field_type == datetime:
        return time_util.now_str()

    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return generate_example_for_model(field_type)

    return None
