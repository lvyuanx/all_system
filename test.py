from weasyprint import HTML

# 从字符串生成 PDF
html_string = """
<html>
  <head>
    <style>
      body { font-family: sans-serif; }
      h1 { color: darkblue; }
    </style>
  </head>
  <body>
    <h1>Hello PDF</h1>
    <p>这是一份由 HTML 渲染的 PDF。</p>
  </body>
</html>
"""

HTML(string=html_string).write_pdf("output.pdf")
