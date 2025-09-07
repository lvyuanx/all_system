from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.template.response import TemplateResponse
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Staff, StaffSalary
from adminfilters.filters import AutoCompleteFilter
from adminfilters.mixin import AdminFiltersMixin
from simpleui.admin import AjaxAdmin
from django.db import transaction

from core.utils import admin_util
from .enums import (
    StaffSalaryStatusChoices,
    StaffSalaryTypeChoices,
    StaffIncomeExpenseChoices,
)
from .machine import StaffSalaryStateMachine
from .signals.signals import after_salary_audit_pass_signal


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):

    list_display = ("user_avatar", "staff_code", "fullname_link")

    search_fields = ("user__full_name", "staff_code")
    autocomplete_fields = ["user"]

    def user_avatar(self, obj):
        avatar = obj.user.avatar
        if avatar:
            return admin_util.AdminListImagePreviewMixin.format_image_lightbox(
                avatar.url, "user_avatar"
            )
        else:
            return ""

    user_avatar.short_description = "头像"

    def fullname_link(self, obj):
        if hasattr(obj, "user"):
            user = obj.user
            url = reverse("admin:core_auth_user_change", args=[user.pk])
            return format_html('<a href="{}">{}</a>', url, user.full_name)
        return "-"

    fullname_link.short_description = "姓名"

    list_display_links = ("staff_code",)


@admin.register(StaffSalary)
class StaffSalaryAdmin(
    AdminFiltersMixin,
    admin_util.AuditAdminMixin,
    admin_util.OperateButtonsMixin,
    admin_util.FilterChangeListMixin,
    AjaxAdmin,
):

    list_display = (
        "salary_serial_number",
        "salary_bind_month",
        "title",
        "staff_code",
        "full_name",
        "salary",
        "income_expense_str",
        "status_tag",
        "salary_type",
        "memo",
        "create_time",
        "operate_buttons"
    )

    operate_buttons_config = [
        {
            "name": "",
            "type": "text",
            "mode": "modal",
            "icon": "fa-solid fa-magnifying-glass",
            "modal_width": "35vw",
            "modal_height": "80vh",
            "url": lambda obj: reverse("admin:staff_staffsalary_change", args=[obj.pk]),
        }
    ]

    sortable_by = "staff_name"

    list_filter = (
        "income_expense",
        "salary_type",
        "staff__user__full_name",
        "status",
        admin_util.CreateTimeQuickFilter,
        ("create_time", admin.DateFieldListFilter),
    )

    search_fields = ("salary_serial_number", "staff__staff_code")

    exclude_fields = (
        "status",
        "audit_memo",
        "staff_code",
        "full_name",
        "phone",
        "title",
        "basic_salary",
        "staff_hourly_wage",
        "income_expense",
        "salary_serial_number",
        "is_release",
        "release_user"
    )

    readonly_fields = ("salary_serial_number",)

    actions = [
        "batch_pass",
        "batch_fail",
        "batch_reject",
        "batch_cancel",
        "batch_correction",
        "batch_release",
    ]

    list_display_links = ("salary_serial_number",)

    autocomplete_fields = ["staff"]

    class StaffSalaryForm(forms.ModelForm):
        class Meta:
            model = StaffSalary
            fields = "__all__"

        def clean(self):
            cleaned_data = super().clean()
            staff = cleaned_data.get("staff")
            year = cleaned_data.get("year")
            month = cleaned_data.get("month")
            salary_type = cleaned_data.get("salary_type")

            if (
                salary_type == StaffSalaryTypeChoices.BASIC_SALARY
                and StaffSalary.objects.filter(
                    staff=staff,
                    is_delete=False,
                    year=year,
                    month=month,
                    salary_type=StaffSalaryTypeChoices.BASIC_SALARY,
                ).exists()
            ):
                raise forms.ValidationError(
                    f"该员工 {year} 年 {month} 月基础工资已存在，请勿重复创建！"
                )

            return cleaned_data

    form = StaffSalaryForm

    def salary_bind_month(self, obj):
        return f"{obj.year}年{obj.month}月"

    salary_bind_month.short_description = "所属月份"

    def income_expense_str(self, obj):
        if obj.income_expense == StaffIncomeExpenseChoices.INCOME:
            return "收入"
        else:
            return f"支出({'已发放' if obj.is_release else '未发放'})"

    income_expense_str.short_description = "收入/支出"

    def status_tag(self, obj):
        status_map = {
            StaffSalaryStatusChoices.UNAUDIT: "#E0CD1E",  # 浅黄色 - 未审核
            StaffSalaryStatusChoices.AUDIT_PASS: "#67C23A",  # 绿色 - 审核通过
            StaffSalaryStatusChoices.PENDING_CORRECTION: "#E6A23C",  # 橙色 - 待修正
            StaffSalaryStatusChoices.CORRECTIONED: "#409EFF",  # 蓝色 - 已修正
            StaffSalaryStatusChoices.AUDIT_REJECT: "#F56C6C",  # 红色 - 审核拒绝
            StaffSalaryStatusChoices.CANCEL: "#909399",  # 灰色 - 取消
        }
        color = status_map.get(obj.status, "black")
        return format_html(
            '<span style="display:inline-block;padding:2px 6px;border-radius:4px;background-color:{};color:white;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_tag.short_description = "状态"

    # region ******************** 根据url传参筛选 start ******************** #
    # skip_filter_fields = ["is_release"]
    # def get_filter_queryset(self, qs, request: HttpRequest):
    #     # 先调用父类方法，处理通用过滤
    #     qs = super().get_filter_queryset(qs, request)
    #     # is_release = request.GET.get("is_release")
    #     # if is_release is not None:
    #     #     if int(is_release):
    #     #         qs = qs.filter(is_release=True)
    #     #     else:
    #     #         qs = qs.filter(
    #     #             Q(is_release=False) | Q(is_release__isnull=True)
    #     #         )
    #     return qs
    # endregion ****************** 根据url传参筛选 end ********************* #

    def get_list_display_links(self, request, list_display):
        # 获取 url 参数
        status = request.GET.get("status", "")
        if str(status) == str(StaffSalaryStatusChoices.PENDING_CORRECTION.value):
            return ("salary_serial_number",)
        return None

    def get_list_display(self, request):
        get_get = request.GET.get
        status = (
            [get_get("status")] if get_get("status") else []
        ) + request.GET.getlist("status")
        if (
            str(StaffSalaryStatusChoices.PENDING_CORRECTION.value) in status
            or str(StaffSalaryStatusChoices.AUDIT_REJECT.value) in status
        ):
            return ("colored_audit_memo",) + self.list_display
        return self.list_display

    def colored_audit_memo(self, obj):
        return format_html('<span style="color:red;">{}</span>', obj.audit_memo or "")

    colored_audit_memo.short_description = "审核备注"

    @admin_util.btn(
        short_description="批量通过",
        icon="el-icon-check",
        type="success",
        confirm="确定通过选中的记录吗？",
    )
    def batch_pass(modeladmin, request, queryset):
        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = StaffSalaryStateMachine(obj, request.user)
                sm.audit_pass()
                sm.save_state()
                count += 1
                admin_util.log_custom_action(request, obj, "审批通过")
                
                # 发送审核通过信号
                after_salary_audit_pass_signal.send(
                    sender=StaffSalary,
                    instance=obj,
                )
        messages.success(request, f"{count} 条记录已批量审批通过。")

    @admin_util.btn(
        short_description="批量发放",
        icon="el-icon-check",
        type="success",
        confirm="确定发放选中的记录吗？",
    )
    def batch_release(modeladmin, request, queryset):
        if queryset.exclude(
            income_expense=StaffIncomeExpenseChoices.EXPENSE,
            status=StaffSalaryStatusChoices.AUDIT_PASS,
        ).exclude(
            Q(is_release=False) | Q(is_release__isnull=True)
        ).exists():
            messages.error(request, "非法发放！")
            return

        count = 0
        with transaction.atomic():
            for obj in queryset:
                obj.is_release = True
                obj.release_user = request.user
                obj.save()
                count += 1
                admin_util.log_custom_action(request, obj, "发放成功")

        messages.success(request, f"{count} 条记录已发放成功。")

    @admin_util.btn(
        short_description="批量完成修正",
        icon="el-icon-check",
        type="success",
        confirm="确定修正选中的记录吗？",
    )
    def batch_correction(modeladmin, request, queryset):
        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = StaffSalaryStateMachine(obj, request.user)
                sm.correction()
                sm.save_state()
                count += 1
                admin_util.log_custom_action(request, obj, "修正完成")
        messages.success(request, f"{count} 条记录已批量修正完成。")

    @admin_util.btn(
        short_description="批量取消",
        icon="fa-solid fa-power-off",
        type="default",
        confirm="确定取消选中的记录吗？",
    )
    def batch_cancel(modeladmin, request, queryset):
        if queryset.exclude(
            status__in=[
                StaffSalaryStatusChoices.UNAUDIT,
                StaffSalaryStatusChoices.PENDING_CORRECTION,
            ]
        ).exists():
            messages.warning(
                request,
                "只有状态为【未审核】、【待修正】的记录才能进行批量取消,请检查勾选项！",
            )
            return
        count = 0
        with transaction.atomic():
            for obj in queryset:
                sm = StaffSalaryStateMachine(obj, request.user)
                sm.cancel()
                sm.save_state()
                count += 1
                admin_util.log_custom_action(request, obj, "工资项取消")
        messages.success(request, f"{count} 条记录已批量取消。")

    @admin_util.btn(
        short_description="批量不通过",
        icon="el-icon-refresh-right",
        type="warning",
        layer={
            "title": "请输入未通过原因",
            "tips": "审批不通过后可以修正信息，重新进行审批！",
            "confirm_button": "确认",
            "cancel_button": "取消",
            "params": [
                {
                    # 这里的type 对应el-input的原生input属性，默认为input
                    "type": "input",
                    # key 对应post参数中的key
                    "key": "memo",
                    # 显示的文本
                    "label": "原因",
                    # 为空校验，默认为False
                    "require": True,
                },
            ],
        },
    )
    def batch_fail(self, request, queryset):
        post = request.POST
        memo = post.get("memo", "").strip()
        if not memo:
            return JsonResponse({"status": "error", "msg": "必须填写不通过原因！"})

        selected = post.get("_selected")
        if not selected:
            return JsonResponse({"status": "error", "msg": "请选择要操作的记录！"})

        count = 0
        BATCH_SIZE = 200  # 可调，避免一次性加载太多对象
        total = queryset.count()

        if total > BATCH_SIZE:
            return JsonResponse(
                {
                    "status": "error",
                    "msg": f"一次最多只能处理 {BATCH_SIZE} 条记录，当前选择了 {total} 条，请缩小范围后再试。",
                }
            )

        with transaction.atomic():
            # 分批迭代 queryset
            for obj in queryset.iterator(chunk_size=BATCH_SIZE):
                sm = StaffSalaryStateMachine(obj, request.user)
                sm.audit_correction()
                sm.save_state(memo)
                count += 1
                admin_util.log_custom_action(request, obj, "审批不通过")

        return JsonResponse({"status": "success", "msg": f"{count} 条记录已操作成功"})

    @admin_util.btn(
        short_description="批量拒绝",
        icon="el-icon-close",
        type="danger",
        layer={
            "title": "请输入拒绝原因",
            "tips": "审批拒绝后，该记录将不可修改！",
            "confirm_button": "确认",
            "cancel_button": "取消",
            "params": [
                {
                    # 这里的type 对应el-input的原生input属性，默认为input
                    "type": "input",
                    # key 对应post参数中的key
                    "key": "memo",
                    # 显示的文本
                    "label": "原因",
                    # 为空校验，默认为False
                    "require": True,
                },
            ],
        },
    )
    def batch_reject(modeladmin, request, queryset):
        post = request.POST
        memo = post.get("memo", "").strip()
        if not memo:
            return JsonResponse({"status": "error", "msg": "必须填写不通过原因！"})

        selected = post.get("_selected")
        if not selected:
            return JsonResponse({"status": "error", "msg": "请选择要操作的记录！"})

        count = 0
        BATCH_SIZE = 200  # 可调，避免一次性加载太多对象
        total = queryset.count()

        if total > BATCH_SIZE:
            return JsonResponse(
                {
                    "status": "error",
                    "msg": f"一次最多只能处理 {BATCH_SIZE} 条记录，当前选择了 {total} 条，请缩小范围后再试。",
                }
            )

        # 分批迭代 queryset
        with transaction.atomic():
            for obj in queryset.iterator(chunk_size=BATCH_SIZE):
                sm = StaffSalaryStateMachine(obj, request.user)
                sm.audit_reject()
                sm.save_state(memo)
                count += 1
                admin_util.log_custom_action(request, obj, "审批拒绝")

        return JsonResponse({"status": "success", "msg": f"{count} 条记录已操作成功"})

    def get_actions(self, request):
        actions = super().get_actions(request)
        # 读取 status
        get_get = request.GET.get
        status = (
            [get_get("status")] if get_get("status") else []
        ) + request.GET.getlist("status")
        income_expense = get_get("income_expense")

        # 只保留当 status=UNAUDIT 时的批量操作
        if str(StaffSalaryStatusChoices.UNAUDIT.value) not in status:
            if "batch_pass" in actions:
                del actions["batch_pass"]
            if "batch_reject" in actions:
                del actions["batch_reject"]
            if "batch_fail" in actions:
                del actions["batch_fail"]

        if str(
            StaffSalaryStatusChoices.AUDIT_PASS.value
        ) not in status or income_expense != str(StaffIncomeExpenseChoices.EXPENSE.value):
            if "batch_release" in actions:
                del actions["batch_release"]

        if (
            status
            and str(StaffSalaryStatusChoices.PENDING_CORRECTION.value) not in status
        ):
            if "batch_cancel" in actions:
                del actions["batch_cancel"]

        if str(StaffSalaryStatusChoices.PENDING_CORRECTION.value) not in status:
            if "batch_correction" in actions:
                del actions["batch_correction"]

        return actions

    def has_add_permission(self, request):
        get_get = request.GET.get
        status = (
            [get_get("status")] if get_get("status") else []
        ) + request.GET.getlist("status")
        if not status:
            return True
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None):
        get_get = request.GET.get
        status = (
            [get_get("status")] if get_get("status") else []
        ) + request.GET.getlist("status")

        if not status and request.user.has_perm("staff.delete_staffsalary"):
            return True
        return False

    
    operate_btn_dict = {
        "view_pdf": {
            "name": "",
            "type": "primary",
            "mode": "modal",  # 也可以改为 "normal"
            "modal_width": "650px",
            "modal_height": "700px",
            "icon": "fa-solid fa-magnifying-glass",
            "onclick":  lambda self, request, obj: self._view_pdf(request, obj),
        },
    }
    
    def _view_pdf(self, request, obj):
        context = {
            "pdf_url": f"", 
        }
        return TemplateResponse(request, "pdf/pdf_preview.html", context)