import os
import uuid
from django.db import models
from django.conf import settings

USER_FILE_PATH = "user/{user_phone}/{business_path}"
USER_AVATAR_PATH = "avatars/{filename}"
CLIENT_FILE_PATH = "client/{business_path}"
CLIENT_LOGO_PATH = "client_logos/{filename}"

def random_filename(filename: str) -> str:
    ext = os.path.splitext(filename)[1]  # 获取文件后缀，如 ".png"
    new_name = f"{uuid.uuid4().hex}{ext}"
    return new_name

def user_avatar_path(instance, filename):
    return USER_FILE_PATH.format(
        user_phone=instance.phone,
        business_path=USER_AVATAR_PATH.format(filename=random_filename(filename=filename))
    )

def client_logo_path(instance, filename):
    return CLIENT_FILE_PATH.format(
        business_path=CLIENT_LOGO_PATH.format(filename=random_filename(filename=filename))
    )

class StructureMoelMixin(models.Model):
    create_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
        verbose_name="创建人",
        related_name="%(class)s_create_user"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    update_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
        verbose_name="更新人",
        related_name="%(class)s_update_user"
    )
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    delete_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
        verbose_name="删除人",
        related_name="%(class)s_delete_user"
    )
    delete_time = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    is_delete = models.BooleanField(default=False, null=True, verbose_name="是否删除")

    class Meta:
        abstract = True


# region ******************** 权限 start ******************** #
class ClassProperty:
    """类属性描述符，兼容 Python 3.11+，替代 @classmethod + @property"""
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, owner):
        return self.fget(owner)


class PermWrapper:
    """单个权限包装类，提供权限名和Permission对象访问"""
    def __init__(self, model_cls, perm_type):
        self.model_cls = model_cls
        self.perm_type = perm_type

    @property
    def codename(self):
        """权限 codename，不带 app_label"""
        return f"{self.perm_type}_{self.model_cls._meta.model_name}"

    @property
    def perm_labelname(self):
        """带 app_label 的权限名"""
        return f"{self.model_cls._meta.app_label}.{self.codename}"

    @property
    def prem(self):
        """返回数据库中的 Permission 对象"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(self.model_cls)
        return Permission.objects.get(content_type=ct, codename=self.codename)

    def __repr__(self):
        return f"<PermWrapper {self.perm}>"


class PermissionHelperMixin(models.Model):
    """
    Django 模型基类，提供便捷访问默认权限的能力：
    Article.view_perm.perm 获取权限字符串 'app_label.view_article'
    Article.view_perm.codename 获取权限 codename 'view_article'
    Article.view_perm.object 获取数据库 Permission 对象
    Article.perms 获取该模型全部默认 Permission 对象列表
    """
    class Meta:
        abstract = True

    _default_perm_types = ("add", "change", "delete", "view")

    @classmethod
    def _perm_wrapper(cls, perm_type):
        if perm_type not in cls._default_perm_types:
            raise AttributeError(f"Permission type '{perm_type}' is not supported")
        return PermWrapper(cls, perm_type)

    @ClassProperty
    def add_perm(cls):
        return cls._perm_wrapper("add")

    @ClassProperty
    def change_perm(cls):
        return cls._perm_wrapper("change")

    @ClassProperty
    def delete_perm(cls):
        return cls._perm_wrapper("delete")

    @ClassProperty
    def view_perm(cls):
        return cls._perm_wrapper("view")

    @ClassProperty
    def perms(cls):
        """获取该模型所有默认权限的 Permission 对象列表"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(cls)
        return list(Permission.objects.filter(content_type=ct))
    
    
    @classmethod
    def get_perms(cls, perm_types):
        """传入权限类型列表，返回带 app_label 的权限字符串列表"""
        return [cls._perm_wrapper(p).perm_labelname for p in perm_types]

    @classmethod
    def get_pack_codenames(cls, perm_types):
        """传入权限类型列表，返回权限 codename 列表"""
        return [cls._perm_wrapper(p).codename for p in perm_types]

    @classmethod
    def get_perm_objs(cls, perm_types):
        """传入权限类型列表，返回权限 Permission 对象列表"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(cls)
        codenames = [cls._perm_wrapper(p).codename for p in perm_types]
        return list(Permission.objects.filter(content_type=ct, codename__in=codenames))   
# endregion ****************** 权限 end ********************* #


