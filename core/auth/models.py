# accounts/models.py
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models import functions
from asgiref.sync import sync_to_async
from core.utils import time_util, model_util
from core.conf import settings


class User(model_util.PermissionHelperMixin, AbstractUser):
    """
    通用用户模型
    """
    
    class Gender(models.TextChoices):
        MALE = 'M', "男"
        FEMALE = 'F', "女"
        UNKNOWN = 'U', "未知"
    
    password = models.CharField(default=settings.DEFAULT_PASSWORD,
                                null=True, max_length=128, verbose_name="密码")
    phone = models.CharField(max_length=20, unique=True, verbose_name="手机号")
    sex = models.CharField(max_length=1, choices=Gender.choices, default=Gender.UNKNOWN, verbose_name="性别")
    age = models.IntegerField(blank=True, null=True, verbose_name="年龄")
    date_joined = models.DateTimeField("注册时间", default=time_util.now)
    avatar = models.ImageField(upload_to=model_util.user_avatar_path, blank=True, 
                               null=True, default=settings.DEFAULT_AVATAR, verbose_name="头像")
    full_name = models.GeneratedField(
        expression=functions.Concat("last_name", "first_name"),
        output_field=models.CharField(max_length=255, null=True, blank=True),
        db_persist=False,
        verbose_name="姓名"
    )
    

    class Meta:
        verbose_name = "用户列表"
        verbose_name_plural = verbose_name
    
    def __str__(self) -> str:
        return f"{self.full_name}:{self.phone if self.phone else '-'}"


class SimpleuiMenus(model_util.PermissionHelperMixin, models.Model):

    name = models.CharField(max_length=255, verbose_name="菜单名称", unique=True)
    icon = models.CharField(max_length=255, null=True, blank=True, verbose_name="图标")
    url = models.CharField(max_length=255, null=True, blank=True, verbose_name="菜单链接")
    new_tab = models.BooleanField(default=False, null=True, verbose_name="新标签页打开")
    path = models.CharField(max_length=255, null=True, blank=True, verbose_name="菜单路径")
    depath = models.IntegerField(default=0, null=True, verbose_name="路径深度")
    permissions = models.ManyToManyField("auth.Permission", blank=True, verbose_name="权限")
    is_active = models.BooleanField(default=True, null=True, verbose_name="是否激活")
    sort_no = models.IntegerField(default=0, null=True, verbose_name="排序")
    
    class Meta:
        verbose_name = "菜单列表"
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name


class PermissionPack(model_util.PermissionHelperMixin, models.Model):

    permissions = models.ManyToManyField("auth.Permission",  blank=True, default=None, verbose_name="权限")
    groups = models.ManyToManyField("auth.Group", blank=True, default=None, verbose_name="权限组", related_name="permission_packs")
    pack_name = models.CharField(max_length=255, verbose_name="权限包名称")
    pack_code = models.CharField(max_length=255, verbose_name="权限包编码")


    def add_group(self, *groups: Group):
        """
        将当前权限包内所有权限添加到指定权限组（支持多个 Group）
        """
        for group in groups:
            if not isinstance(group, Group):
                raise ValueError("参数必须是 django.contrib.auth.models.Group 实例")
            group.permissions.add(*self.permissions.all())
        self.groups.add(*groups)
    
    @sync_to_async
    def aadd_group(self, *groups: Group):
        self.add_group(*groups)


    def remove_groups(self, *groups: Group):
        """
        将当前权限包内所有权限从指定权限组移除，
        如果没有传入权限组参数，则从关联的所有权限组移除。
        """
        if groups:
            target_groups = groups
        else:
            target_groups = self.groups.all()

        if not target_groups:
            return

        perms = self.permissions.all()
        if perms.exists():
            for group in target_groups:
                group.permissions.remove(*perms)
        
        self.groups.remove(*target_groups)
            
    
    @sync_to_async
    def aremove_groups(self, *groups: Group):
        self.remove_groups(*groups)

    
    def remove_permissions(self, *permissions: Permission):
        """
        将当前权限包内所有权限移除，
        如果传入权限参数，则移除指定权限，否则移除权限包内所有权限
        """
        if permissions:
            target_perms = permissions
        else:
            target_perms = self.permissions.all()

        if not target_perms:
            return  # 没权限就直接返回

        # 批量移除
        self.permissions.remove(*target_perms)
    
    
    @sync_to_async
    def aremove_permissions(self, *permissions: Permission):
        self.remove_permission(*permissions)
    
    
    def __str__(self):
        return f"{self.pack_code}:{self.pack_name}"
                
