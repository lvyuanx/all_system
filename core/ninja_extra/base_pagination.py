from typing import TypeVar, Generic, List, Type, Any
from ninja import Schema
from ninja.pagination import AsyncPaginationBase
from pydantic import Field
from core.ninja_extra.response_schema import SuccessResponse
from django.db.models import QuerySet

T = TypeVar("T")


class AsyncCustomLimitOffsetPagination(AsyncPaginationBase):
    """
    自定义异步分页器
    - 输入参数: page / page_size
    - 输出参数: current_page / page_size / total_count / data
    - 返回格式继承 SuccessResponse
    """

    items_attribute = "data"

    class Input(Schema):
        page: int = Field(default=1, ge=1, description="当前页，最小为1")
        page_size: int = Field(default=15, ge=1, le=500, description="每页数量，最大500")

    class Output(SuccessResponse):
        current_page: int = Field(default=1, description="当前页")
        page_size: int = Field(default=15, description="每页数量")
        total_count: int = Field(default=0, description="总数量")
        data: List[T] = Field(default=[], description="分页数据")

    def paginate_queryset(self, *args, **kwargs):
        """同步模式禁用"""
        raise NotImplementedError("仅支持异步分页")

    async def apaginate_queryset(
        self,
        queryset: QuerySet,
        pagination: Input,
        **params: Any,
    ) -> Output[T]:
        # ✅ page 从 1 开始，内部换算 offset
        page = pagination.page
        page_size = pagination.page_size
        offset = (page - 1) * page_size
        limit = page_size

        total_count = await self._aitems_count(queryset)

        if hasattr(queryset, "__aiter__"):  # 异步 QuerySet
            items = [obj async for obj in queryset[offset:offset + limit]]
        else:  # 普通 Django ORM QuerySet
            items = list(queryset[offset:offset + limit])

        return self.Output(
            current_page=page,
            page_size=page_size,
            total_count=total_count,
            data=items,
        )
