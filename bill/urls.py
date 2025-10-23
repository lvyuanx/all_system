from django.urls import path
from .page_views.bill_page import preview_bill_pdf_view, dynamic_rendering_bill_html_view

app_name = "bill"

urls = [
    path("bill/bill/preview/pdf/<int:id>/", preview_bill_pdf_view, name="preview_bill_pdf_view"),
    path("bill/billtemplate/dynamic_rendering_bill_html/<int:id>/", dynamic_rendering_bill_html_view, name="dynamic_rendering_bill_html_view"),
]