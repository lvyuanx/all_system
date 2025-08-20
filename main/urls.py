"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

from core.ninja_extra.urls import urls as NINJA_URLS
from core.auth.urls import urls as AUTH_URLS

urlpatterns = [
    path('admin/', include(AUTH_URLS)),
    path('admin/', admin.site.urls),
] + NINJA_URLS

if settings.DEBUG:
    # 开发环境下服务静态文件
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # 服务媒体文件
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
