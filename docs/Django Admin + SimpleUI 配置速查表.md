# 📑 Django Admin + SimpleUI 配置速查表

## 🔍 列表页 (List View)
| 配置项 | 作用 | 示例 |
|--------|------|------|
| `list_display` | 显示哪些字段 | `list_display = ("id", "name", "status")` |
| `list_display_links` | 哪些字段可点击进入详情页 | `list_display_links = ("id", "name")` |
| `list_editable` | 列表页可直接编辑字段 | `list_editable = ("status",)` |
| `ordering` | 默认排序规则 | `ordering = ("-id",)` |
| `list_per_page` | 每页显示条数 | `list_per_page = 20` |
| `list_max_show_all` | “显示全部”的最大数量 | `list_max_show_all = 200` |
| `empty_value_display` | 空值显示内容 | `empty_value_display = "-"` |
| `date_hierarchy` | 日期层级导航 | `date_hierarchy = "create_time"` |

---

## 🔎 搜索与过滤 (Search & Filter)
| 配置项 | 作用 | 示例 |
|--------|------|------|
| `search_fields` | 支持搜索的字段（支持 `^`, `=`, `@` 前缀） | `search_fields = ("name", "email")` |
| `list_filter` | 右侧过滤器 | `list_filter = ("status", "create_time")` |
| `filter_horizontal` | 多对多字段更好用的横向选择框 | `filter_horizontal = ("groups",)` |
| `filter_vertical` | 多对多字段纵向选择框 | `filter_vertical = ("permissions",)` |

---

## 📝 表单页 (Form View)
| 配置项 | 作用 | 示例 |
|--------|------|------|
| `fields` | 指定表单显示字段 | `fields = ("name", "email", "status")` |
| `exclude` | 排除字段 | `exclude = ("password",)` |
| `readonly_fields` | 只读字段 | `readonly_fields = ("create_time",)` |
| `fieldsets` | 分组显示字段 | `fieldsets = ((None, {"fields": ("name", "email")}), ("高级", {"fields": ("status",)}))` |
| `save_on_top` | 保存按钮显示在顶部 | `save_on_top = True` |
| `save_as` | 编辑时允许“另存为新对象” | `save_as = True` |

---

## ⚡ 操作与按钮 (Actions & Buttons)
| 配置项 / 方法 | 作用 | 示例 |
|---------------|------|------|
| `actions` | 批量操作 | `actions = ["export_to_excel"]` |
| `actions_on_top` | 批量操作按钮显示在顶部 | `actions_on_top = True` |
| `actions_on_bottom` | 批量操作按钮显示在底部 | `actions_on_bottom = False` |
| `formfield_overrides` | 修改表单字段控件类型 | `formfield_overrides = {models.TextField: {"widget": forms.Textarea}}` |
| `自定义按钮` | 使用 SimpleUI 按钮（ElementUI 风格） | `format_html('<button class="el-button el-button--primary">查看</button>')` |

---

## 🔒 权限控制 (Permissions)
| 方法 | 作用 | 示例 |
|------|------|------|
| `has_add_permission` | 是否允许新增 | `def has_add_permission(self, request): return True` |
| `has_change_permission` | 是否允许修改 | `def has_change_permission(self, request, obj=None): return request.user.is_superuser` |
| `has_delete_permission` | 是否允许删除 | `def has_delete_permission(self, request, obj=None): return False` |
| `get_queryset` | 默认数据过滤（常用于软删除） | `def get_queryset(self, request): return super().get_queryset(request).filter(is_delete=False)` |

---

## 🎨 SimpleUI 全局配置 (settings.py)
| 配置项 | 作用 | 示例 |
|--------|------|------|
| `SIMPLEUI_DEFAULT_THEME` | 默认主题 | `SIMPLEUI_DEFAULT_THEME = "dark"` |
| `SIMPLEUI_LOGO` | 后台左上角 logo | `SIMPLEUI_LOGO = "/static/img/logo.png"` |
| `SIMPLEUI_HOME_TITLE` | 首页标题 | `SIMPLEUI_HOME_TITLE = "管理后台"` |
| `SIMPLEUI_HOME_INFO` | 是否显示首页信息 | `SIMPLEUI_HOME_INFO = False` |
| `SIMPLEUI_HOME_PAGE` | 自定义首页地址 | `SIMPLEUI_HOME_PAGE = "/admin/dashboard/"` |
| `SIMPLEUI_HIDE_APPS` | 隐藏指定应用 | `SIMPLEUI_HIDE_APPS = ["auth"]` |
| `SIMPLEUI_HIDE_MODELS` | 隐藏指定模型 | `SIMPLEUI_HIDE_MODELS = ["app.Model"]` |
| `SIMPLEUI_ANALYSIS` | 是否开启统计上报 | `SIMPLEUI_ANALYSIS = False` |
| `SIMPLEUI_CONFIG` | 菜单配置 | `SIMPLEUI_CONFIG = {"system_keep": True, "menu": [...]}` |
| `SIMPLEUI_INDEX` | 自定义首页路由 | `SIMPLEUI_INDEX = "/admin/index/"` |
