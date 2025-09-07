from django.urls import path
from .page_views.bill_page import preview_bill_pdf_view

app_name = "bill"

urls = [
    path("bill/preview/pdf/<int:id>/", preview_bill_pdf_view, name="preview_bill_pdf_view"),
]