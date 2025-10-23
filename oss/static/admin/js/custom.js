async function refresh_bill_pdf(event, pk) {
    await this.SimpleUIExtra.ElMessageBox.confirm("确定要重新票据吗？")
    await this.request.get("/bill/refresh_bill_pdf", {pk})
    this.SimpleUIExtra.ElMessage.success("操作成功")
}