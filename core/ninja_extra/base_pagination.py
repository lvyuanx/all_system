from functools import wraps
import json
from typing import Callable, Generic, List, Optional, Type, TypeVar, Dict, Any, Union

from django.db.models import QuerySet
from ninja import Query, Schema, Field

T = TypeVar("T")


class AsyncLimitOffsetPagination:
    """
    通用异步分页器（支持 Django ORM 同步/异步）
    支持自定义输入/输出字段映射
    """

    InputSource = Query

    # 默认输出字段映射，可在子类中覆盖
    output_field_map: Dict[str, str] = {
        "current_page": "current_page",
        "page_size": "page_size",
        "total_count": "total_count",
        "items": "items",
    }

    # 默认输入字段映射，可在子类中覆盖
    input_field_map: Dict[str, str] = {
        "page": "page",
        "page_size": "page_size",
    }

    # ================= 输入 Schema =================
    class Input(Schema):
        page: int = Field(default=1, ge=1, description="当前页，最小为1")
        page_size: int = Field(default=15, ge=1, le=500, description="每页数量，最大500")
        filter: Optional[str] = Field(None, description="筛选条件, json字符串")
        sort: Optional[str] = Field(None, description="排序条件, json字符串")

    # ================= 输出 Schema =================
    class Output(Schema, Generic[T]):
        current_page: int = Field(..., description="当前页")
        page_size: int = Field(..., description="每页数量")
        total_count: int = Field(..., description="总数量")
        items: List[T] = Field(..., description="分页数据")

    # ================= 可扩展 hook =================
    async def aprocess_result(self, results: List) -> List:
        """分页后处理结果，比如序列化或数据脱敏"""
        return results

    async def _aitems_count(self, queryset: QuerySet) -> int:
        """统计总数，可子类重写以优化性能"""
        try:
            return await queryset.acount()
        except AttributeError:
            return queryset.count() if hasattr(queryset, "count") else len(queryset)

    async def afilter_queryset(self, queryset: QuerySet, input_filter: dict):
        """过滤数据，根据前端传入的参数进行过滤"""
        return queryset

    # ================= 内部工具方法 =================
    def _is_async_queryset(self, queryset: QuerySet) -> bool:
        """判断是否异步 QuerySet"""
        return hasattr(queryset, "aall") or hasattr(queryset, "__aiter__")

    def output(self, current_page: int, page_size: int, total_count: int, items: List[T]) -> Schema:
        """
        构造输出 Schema
        使用动态生成子类解决泛型 Pydantic 不能直接实例化的问题
        """
        # 动态创建 Output 子类，指定泛型类型 T
        OutputSchema = type(
            "OutputSchema",
            (self.Output,),
            {"__annotations__": {"current_page": int, "page_size": int, "total_count": int, "items": List[type(items[0]) if items else Any]}}
        )

        payload = {
            self.output_field_map["current_page"]: current_page,
            self.output_field_map["page_size"]: page_size,
            self.output_field_map["total_count"]: total_count,
            self.output_field_map["items"]: items,
        }

        return OutputSchema(**payload)

    # ================= 主流程 =================
    async def apaginate_queryset(self, queryset: QuerySet, pagination_input: Input) -> Schema:
        # 过滤条件
        filter_json = pagination_input.filter
        if filter_json:
            filter_dict = json.loads(filter_json)
            queryset = await self.afilter_queryset(queryset, filter_dict)

        # 排序条件
        sort_json = pagination_input.sort
        if sort_json:
            sort_list = json.loads(sort_json)
            queryset = queryset.order_by(*sort_list)

        # 使用 input_field_map 获取分页参数
        page = getattr(pagination_input, self.input_field_map["page"])
        page_size = getattr(pagination_input, self.input_field_map["page_size"])
        offset = (page - 1) * page_size
        limit = page_size

        total_count = await self._aitems_count(queryset)

        # 获取分页数据
        if self._is_async_queryset(queryset):
            items = [obj async for obj in queryset[offset : offset + limit]]
        else:
            items = list(queryset[offset : offset + limit])

        items = await self.aprocess_result(items)

        return self.output(page, page_size, total_count, items)


# ================= 分页装饰器 =================
def paginate(pagination_class: Type[AsyncLimitOffsetPagination]):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, ninja_pagination=None, **kwargs):
            # ninja_pagination 已经是 Input 实例
            pagination_input = ninja_pagination

            # 执行原函数获取 queryset
            queryset = await func(*args, **kwargs)

            paginator = pagination_class()
            return await paginator.apaginate_queryset(queryset, pagination_input)

        return wrapper

    return decorator
