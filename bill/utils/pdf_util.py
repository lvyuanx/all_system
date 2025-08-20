# -*-coding:utf-8 -*-

"""
# File       : pdf_util.py
# Time       : 2025-08-07 15:30:23
# Author     : lyx
# version    : python 3.11
# Description: pdf工具
"""
import os
import uuid
from django.conf import settings
from jinja2 import Template
import pdfkit

def jinja2_to_pdf(template_str: str, params: dict):
    filename = f"{uuid.uuid4().hex}.pdf"
    media_path = os.path.join("pdf", filename)  # 保存到 MEDIA_ROOT/pdf/ 下
    output_path = os.path.join(settings.MEDIA_ROOT, media_path)
    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    template = Template(template_str)
    rendered_html = template.render(**params)
    pdfkit.from_string(rendered_html, output_path)
    return media_path
    
    
    
if __name__ == "__main__":
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #2c3e50; }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
            }
            td, th {
                border: 1px solid #ddd;
                padding: 8px;
            }
            .footer {
                margin-top: 40px;
                font-size: 12px;
                color: #999;
            }
        </style>
    </head>
    <body>

        <h1>员工信息表</h1>

        <p>姓名：{{ name }}</p>
        <p>工号：{{ staff_id }}</p>
        <p>部门：{{ department }}</p>
        <p>入职日期：{{ hire_date }}</p>

        <h2>本月考勤</h2>
        <table>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
                {% for record in attendance %}
                <tr>
                    <td>{{ record.date }}</td>
                    <td>{{ record.status }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer">
            本报告由系统自动生成于：{{ now }}
        </div>

    </body>
    </html>
    """
    from datetime import datetime
    param = {
        'name': '张三',
        'staff_id': 'A123456',
        'department': '技术部',
        'hire_date': '2021-03-15',
        'now': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'attendance': [
            {'date': '2025-08-01', 'status': '出勤'},
            {'date': '2025-08-02', 'status': '请假'},
            {'date': '2025-08-03', 'status': '出勤'},
        ]
    }

    jinja2_to_pdf(
        template_str=template,
        params=param
    )
