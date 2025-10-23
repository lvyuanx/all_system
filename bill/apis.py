from .views import refresh_bill_pdf_view

apis = {
    "": [
        (
            "A0",
            "refresh_bill_pdf",
            refresh_bill_pdf_view.View,
            "更新票据PDF文件",
        ),
    ]
}
