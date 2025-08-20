from django.http import HttpRequest
from core.auth.models import SimpleuiMenus

def get_dynamic_menus(request: HttpRequest):
    """
    从 SimpleuiMenus 表中构建符合 SimpleUI 格式的 menus 配置，支持多级菜单，并根据用户权限进行过滤。
    超级管理员不受权限限制。
    """
    user_permissions = request.user.get_all_permissions()

    menus = SimpleuiMenus.objects.filter(is_active=True).order_by('sort_no')

    # 构建路径 => 子菜单映射
    children_map = {}
    path_map = {}
    for menu in menus:
        path_map[menu.path] = menu
        parts = menu.path.strip().split('/')
        if len(parts) > 1:
            parent_path = '/'.join(parts[:-1])
            children_map.setdefault(parent_path, []).append(menu)
        else:
            children_map.setdefault(None, []).append(menu)

    # 权限判断函数
    def has_permission(menu: SimpleuiMenus) -> bool:
        # 超级管理员拥有所有权限
        if request.user.is_superuser:
            return True

        perms = menu.permissions.all()
        # 没设置权限，默认可见
        if not perms:
            return True

        for perm in perms:
            perm_str = f"{perm.content_type.app_label}.{perm.codename}"
            if perm_str in user_permissions:
                return True
        return False

    # 递归构建菜单节点
    def build_node(menu: SimpleuiMenus):
        if menu.path in children_map:
            # 有子菜单
            child_nodes = [build_node(child) for child in children_map[menu.path]]
            # 过滤掉无权限的子菜单
            child_nodes = [node for node in child_nodes if node is not None]

            if not child_nodes:
                # 如果子菜单都没权限，判断本菜单是否有权限
                if not has_permission(menu):
                    return None

            return {
                "name": menu.name,
                "icon": menu.icon or '',
                "models": child_nodes if child_nodes else None,
                "url": menu.url if not child_nodes else '',
            }
        else:
            # 叶子菜单，直接判断权限
            if not has_permission(menu):
                return None
            return {
                "name": menu.name,
                "icon": menu.icon or '',
                "url": menu.url or '',
            }

    # 构建最终菜单树，只保留有权限的顶级节点
    return [
        node for node in
        (build_node(top) for top in children_map.get(None, []))
        if node is not None
    ]



    