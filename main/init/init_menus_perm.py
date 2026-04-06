import logging

from django.contrib.auth.models import Permission

from core.auth.models import SimpleuiMenus, MobileMenus

logger = logging.getLogger(__name__)


menus_perm_dict = {
    "版式管理/版式库": ["view_pattern"],
    "版式管理/图库搜索": ["view_pattern"],
    
    "站点管理/地址管理": ["view_siteaddress"],
    "站点管理/系统站点": ["view_syssite"],
    
    "订单管理/所有订单": ["view_order"],
    "订单管理/已完成": ["view_order"],
    "订单管理/订单池": ["add_order", "confirm_order"],
    "订单管理/待排产": ["schedule_order"],
    "订单管理/待生产": ["production_order"],
    "订单管理/生产中": ["production_order"],
    "订单管理/待发货": ["ship_order"],
    "订单管理/待签收": ["complete_order"],
    "订单管理/已取消": ["cancel_order"],
    
    
    "工资管理/工资发放": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/快捷操作": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/待审批": ["audit_staffsalary"],
    "工资管理/审核通过": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/已取消": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/已拒绝": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/待修正": ["view_staffsalary", "view_staffsalaryca"],
    "工资管理/工资库": ["view_staffsalary", "view_staffsalaryca"],
    
    "用户管理/角色管理": ["view_group"],
    "用户管理/用户列表": ["view_user"],
    
    "客户管理/客户列表": ["view_client"],
    
    "员工管理/员工列表": ["view_staff"],
    
    "票据管理/模板管理": ["view_billtemplate"],
    "票据管理/票据库": ["view_bill"],
    
    "菜单管理/菜单列表": ["view_simpleuimenus"],


}

mobile_menus_perm_dict = {
    "版式管理/版式库": ["view_pattern"],
    "版式管理/图库搜索": ["view_pattern"],
    "订单管理": ["view_order"],
}


def _bind_menu_permissions(menu_model, path_perm_dict: dict[str, list[str]]):
    # 根据配置查询到所有的菜单项
    menus = menu_model.objects.filter(path__in=path_perm_dict.keys())

    # 根据配置查询到所有的权限
    codenames = []
    for cs in path_perm_dict.values():
        codenames.extend(cs)
    perms = Permission.objects.filter(codename__in=codenames)
    codename_dict = {perm.codename: perm for perm in perms}

    # 给菜单绑定权限
    for menu in menus:
        menu.permissions.add(*[codename_dict[codename] for codename in path_perm_dict[menu.path]])


def init_menus_perm():
    _bind_menu_permissions(SimpleuiMenus, menus_perm_dict)
    init_mobile_menus_perm()


def init_mobile_menus_perm():
    _bind_menu_permissions(MobileMenus, mobile_menus_perm_dict)
