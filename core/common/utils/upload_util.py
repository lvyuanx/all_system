import os
import uuid

from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from core.utils import time_util


def resource_upload_to(instance, filename: str):
    """
    根据业务模型和分类动态生成上传路径：
    /media/resources/<model_name>/<category>/<YYYY/MM/DD>/<stored_filename>
    """
    date_path = time_util.now().strftime("%Y/%m/%d")

    # 优先使用业务模型提供的 resource_category 属性
    category = getattr(instance, "category", None) or "common"
    if instance.content_object and hasattr(instance.content_object, "resource_category"):
        category = instance.content_object.resource_category

    model_name = instance.content_type.model if instance.content_type else "unknown"

    return os.path.join("resources", model_name, category, date_path, instance.name)


class ResourceAttachContext:
    """
    用于给任意模型批量创建 Resource 的上下文管理器。
    自动管理事务和资源绑定。

    示例：
        with ResourceAttachContext(uploader_id=request.user.id) as ctx:
            rid = ctx.upload(request.FILES["file"], category="pattern")
            ctx.link(rid, object_id=pattern.id)
    """

    def __init__(self, uploader_id=None):
        self.uploader_id = uploader_id
        self.rid_dict = {}
        self._transaction = None
        self._committed = False

    def __enter__(self):
        """进入 with 块，开启事务"""
        self._transaction = transaction.atomic()
        self._transaction.__enter__()
        return self

    def upload(self, file, category=None, content_type=None, obj=None):
        """
        上传文件并创建 Resource 记录。
        返回 Resource.id
        """
        from ..models import Resource
        if not file:
            raise ValueError("file 参数不能为空")
        if not content_type and not obj:
            raise ValueError("content_type 和 obj 参数不能同时为空")
        
        if not content_type:
            content_type = ContentType.objects.get_for_model(obj)
            
        res = Resource(
            file=file,
            category=category,
            uploader_id=self.uploader_id,
            content_type=content_type,
        )
        res.save()
        rid = res.pk
        self.rid_dict[rid] = res
        return rid

    def link(self, rid, object_id):
        """
        将指定 rid 的 Resource 绑定到业务对象。
        """
        assert rid in self.rid_dict, f"Resource ID {rid} not found in context"
        res = self.rid_dict[rid]
        res.object_id = object_id
        res.save(update_fields=["object_id"])

    def commit(self):
        """手动提交（可选）"""
        if self._transaction and not self._committed:
            self._transaction.__exit__(None, None, None)
            self._committed = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        """离开 with 块时提交或回滚事务"""
        if exc_type is not None:
            # 出现异常时回滚
            if self._transaction:
                self._transaction.__exit__(exc_type, exc_val, exc_tb)
            return False  # 继续抛出异常
        else:
            # 正常退出，提交事务
            if self._transaction and not self._committed:
                self._transaction.__exit__(None, None, None)
                self._committed = True
        return True


        

