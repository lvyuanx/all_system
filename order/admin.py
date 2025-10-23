from django.contrib import admin

from order.models import Order, OrderItem
from core.admin_extra.mixins import AuditAdminMixin
from core.admin_extra.forms import AdminFormImageUploadForm

@admin.register(Order)
class OrderAdmin(AuditAdminMixin, admin.ModelAdmin):
    
    pass


@admin.register(OrderItem)
class OrderItemAdmin(AuditAdminMixin, admin.ModelAdmin):
    
    class Form(AdminFormImageUploadForm):
        upload_image_fields = ("pattern_png",)

        class Meta:
            model = OrderItem
            fields = "__all__"
    
    form = Form