# -*-coding:utf-8 -*-
"""
# File       : docs_login.py
# Time       : 2025-10-28 10:37:39
# Author     : lyx
# version    : python 3.11
# Description: 文档登录（使用 Django 认证系统）
"""
import json
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.contrib.auth import authenticate

from core.conf import settings
from core.utils import token_util

logger = logging.getLogger(__name__)

DOC_URL = f"/{settings.NINJA_BASE_URL}docs"
TOKEN_TAG = getattr(settings, "TOKEN_TAG", "X-Authorization")
TOKEN_ORIGIN = settings.TOKEN_ORIGIN  # token来源
TOKEN_TAG = settings.TOKEN_TAG  # token标记名称
SECRET_KEY = settings.SECRET_KEY
TOKEN_EXPIRE = settings.TOKEN_EXPIRE  # token过期时间
token_handler = token_util.tk_handler_dict[TOKEN_ORIGIN]

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="zh-cn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统登录</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #f0f2f5 0%, #d9e2ec 100%);
            display: flex; justify-content: center; align-items: center;
            height: 100vh;
        }
        .login-box {
            width: 100%; max-width: 360px;
            padding: 30px 25px; background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
        }
        .login-box h2 { margin-bottom: 20px; color: #333333; }
        .login-box input {
            width: 100%; padding: 12px 15px; margin: 10px 0;
            border: 1px solid #ccd0d5; border-radius: 6px; font-size: 14px;
        }
        .login-box input:focus { border-color: #007bff; outline: none; }
        .login-box button {
            width: 100%; padding: 12px; margin-top: 15px;
            background: #007bff; color: #fff; font-size: 16px;
            border: none; border-radius: 6px; cursor: pointer;
        }
        .login-box button:hover { background: #0056b3; }
        .error { color: #e74c3c; font-size: 14px; margin-top: 10px; min-height: 18px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>系统登录</h2>
        <div id="error" class="error"></div>
        <input id="username" type="text" placeholder="用户名" required>
        <input id="password" type="password" placeholder="密码" required>
        <button id="loginBtn">登 录</button>
    </div>

    <script>
        const loginBtn = document.getElementById("loginBtn");
        const errorBox = document.getElementById("error");

        loginBtn.addEventListener("click", async () => {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();
            errorBox.textContent = "";

            if (!username || !password) {
                errorBox.textContent = "请输入用户名和密码";
                return;
            }

            loginBtn.disabled = true;
            loginBtn.textContent = "登录中...";

            try {
                const res = await fetch("/docs_login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password }),
                    credentials: "same-origin"
                });

                const data = await res.json();
                if (data.code === 200) {
                    window.location.href = data.next || "/";
                } else {
                    errorBox.textContent = data.msg || "登录失败";
                }
            } catch (err) {
                errorBox.textContent = "请求失败，请稍后再试";
                console.error(err);
            } finally {
                loginBtn.disabled = false;
                loginBtn.textContent = "登 录";
            }
        });

        document.addEventListener("keydown", function(e){
            if(e.key === "Enter"){
                loginBtn.click();
            }
        });
    </script>
</body>
</html>
"""

class DocsLoginMiddlware:
    """基于 Django 用户系统的登录中间件"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        path = request.path

        # 不拦截普通请求
        if not path.startswith(DOC_URL) and not path.startswith("/docs_logout") and not path.startswith("/docs_login"):
            return self.get_response(request)

        if path.startswith("/docs_login"):
            if request.method != "POST":
                return HttpResponse(LOGIN_HTML, content_type="text/html")
            return self.handle_login(request)

        if path.startswith("/docs_logout"):
            return self.handle_logout(request)

        # 拦截 docs 请求，检查登录状态
        return self.handle_docs_request(request)

    # ---------------- 登录逻辑 ----------------
    def handle_login(self, request: HttpRequest):
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")
        except Exception:
            return JsonResponse({"code": 0, "msg": "请求数据异常"}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({"code": 0, "msg": "用户名或密码错误"}, status=401)
        
        new_token = token_util.create_token(
            payload={
                "uid": user.pk,
            },
            secret=SECRET_KEY,
            expire_seconds=TOKEN_EXPIRE
        ) # 生成token
        request.new_token = new_token
        response = JsonResponse({"code": 200, "msg": "登录成功", "next": DOC_URL})
        token_util.tk_handler_dict[TOKEN_ORIGIN].set(response, TOKEN_TAG, new_token)
        return response

    # ---------------- 登出逻辑 ----------------
    def handle_logout(self, request: HttpRequest):
        response = self.to_login()
        token_handler.remove(response, TOKEN_TAG)
        return response

    # ---------------- 文档访问验证 ----------------
    def handle_docs_request(self, request: HttpRequest):
        token = token_handler.get(request, TOKEN_TAG)
        if not token:
            return self.to_login()
        return self.get_response(request)

    # ---------------- 跳转到登录页 ----------------
    def to_login(self):
        return HttpResponse(LOGIN_HTML, content_type="text/html")
