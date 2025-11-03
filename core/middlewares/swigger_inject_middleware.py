# your_app/middleware.py
from django.utils.deprecation import MiddlewareMixin
import re

from core.conf import settings

DOC_PATH_PREFIX = f"/{settings.NINJA_BASE_URL}docs"   # 或者你 swagger 的实际路径，如 "/api/docs" 或 "/v1/api/docs"
INJECT_SCRIPT_TAGS = """
<script src="/static/ninja/logout.js"></script>
<script src="/static/ninja/search.js"></script>
"""

class SwaggerInjectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            path = request.path
            # 只针对 swagger docs 页面和 HTML 响应
            if not path.startswith(DOC_PATH_PREFIX):
                return response

            content_type = response.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                return response

            # 只注入一次（避免重复注入）
            content = response.content.decode(response.charset or 'utf-8')
            if INJECT_SCRIPT_TAGS in content:
                return response

            # 插入到 </body> 前；如果没有 body，则追加到末尾
            if '</body>' in content:
                content = re.sub(r'</body>', INJECT_SCRIPT_TAGS + '</body>', content, flags=re.IGNORECASE)
            else:
                content = content + INJECT_SCRIPT_TAGS

            response.content = content.encode(response.charset or 'utf-8')
            # 修正 Content-Length
            if response.has_header('Content-Length'):
                response['Content-Length'] = str(len(response.content))
        except Exception:
            # 注：不要抛异常影响正常页面加载，记录或忽略
            import logging
            logging.exception("swagger inject failed")
        return response
