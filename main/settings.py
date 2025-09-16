from pathlib import Path
from core.utils.config_util import merge_config


# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# 用于加密签名 Django 项目中的数据，如会话、密码重置令牌等
SECRET_KEY = "django-insecure-#9rd5_+z@*)=-kqwzt@5x(v76bg#hgdt!=i2gq6en&#v_j7&g4"

# SECURITY WARNING: don"t run with debug turned on in production!
# 调试模式开关，开发时设为 True，生产环境应设为 False
DEBUG = merge_config("DEBUG", True)

# 允许访问该 Django 项目的主机列表
# 在生产环境中需要设置具体的域名或 IP 地址
ALLOWED_HOSTS = ["*"]

# 已安装的应用列表
# Django 会自动在这些应用中查找模型、视图、模板等
INSTALLED_APPS = [
    "simpleui",                      # Django 主题
    "django.contrib.admin",          # Django 管理后台
    "django.contrib.auth",           # 认证系统
    "django.contrib.contenttypes",   # 内容类型框架
    "django.contrib.sessions",       # 会话框架
    "django.contrib.messages",       # 消息框架
    "django.contrib.staticfiles",    # 静态文件管理
    "ninja",                         # ninja 框架
    "core.auth",                     # 认证系统
    "core.ninja_extra",              # ninja 框架扩展
    "core.common",                   # 公共模块
    "staff",                         # 员工管理
    "bill",                          # 票据管理
    "client_mgmt",                   # 客户管理
]

# 中间件列表
# 中间件是在请求和响应过程中处理请求的钩子框架
MIDDLEWARE = [
    "core.middlewares.status_code_middleware.StatusCodeMiddleware", # 异常转换中间件
    
    "django.middleware.security.SecurityMiddleware",       # 安全相关中间件
    "django.contrib.sessions.middleware.SessionMiddleware", # 会话中间件
    "django.middleware.common.CommonMiddleware",          # 通用中间件
    "django.middleware.csrf.CsrfViewMiddleware",          # CSRF 保护中间件
    "django.contrib.auth.middleware.AuthenticationMiddleware", # 认证中间件
    "django.contrib.messages.middleware.MessageMiddleware",   # 消息中间件
    "django.middleware.clickjacking.XFrameOptionsMiddleware", # 点击劫持保护中间件
    
    "core.middlewares.docs_login_middleware.DocsLoginMiddlware", # 文档登录中间件
    "core.middlewares.admin_login_to_jwt_middleware.AdminLoginToJwtMiddleware", # admin登录中间件
    "core.middlewares.jwt_middleware.JWTMiddleware", # jwt认证中间件
    "core.middlewares.simpleui_menus_middleware.SimpleuiMenusMiddlware", # simpleui菜单中间件
]

# 身份验证后端
# AUTHENTICATION_BACKENDS = ( 
#     'django.contrib.auth.backends.ModelBackend', 
#     'guardian.backends.ObjectPermissionBackend', # 权限控制
# ) 

# 根 URL 配置文件
# 指定项目主 URL 配置文件的位置
ROOT_URLCONF = "main.urls"
ROOT_APICONF = "main.apis"

# 模板配置
# 定义模板引擎的设置
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # 使用 Django 模板引擎
        "DIRS": [
            BASE_DIR / "core/ninja_extra/templates",  # 添加自定义ninja模板目录
            BASE_DIR / "core/templates",  # 自定义模板
        ],                                                    # 模板目录列表
        "APP_DIRS": True,                                              # 是否在每个已安装应用中查找模板目录
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",      # 添加请求上下文处理器
                "django.contrib.auth.context_processors.auth",     # 添加认证上下文处理器
                "django.contrib.messages.context_processors.messages", # 添加消息上下文处理器
            ],
        },
    },
]

# WSGI 应用对象路径
# 指定 WSGI 应用对象，用于部署到生产服务器
WSGI_APPLICATION = "main.wsgi.application"
ASGI_APPLICATION = "main.asgi.application"

# 数据库配置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": merge_config("DB_NAME", "all_system"),
        "USER": merge_config("DB_USER"),
        "PASSWORD": merge_config("DB_PASSWORD"),
        "HOST": merge_config("DB_HOST", "127.0.0.1"),
        "PORT":  merge_config("DB_PORT", "3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}


# 密码验证器
# 定义密码强度验证规则
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },  # 验证密码是否与用户属性（如用户名）相似
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },  # 验证密码最小长度
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },  # 验证密码是否为常用密码
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },  # 验证密码是否全为数字
]

# 国际化设置
LANGUAGE_CODE = "zh-hans"    # 语言代码改为简体中文
TIME_ZONE = "Asia/Shanghai"  # 时区改为上海时区
USE_I18N = True              # 是否启用国际化
USE_TZ = True                # 是否使用时区

# 静态文件设置（CSS, JavaScript, Images）
STATIC_URL = "static/"     # 静态文件的 URL 前缀
STATIC_ROOT = BASE_DIR /  "oss/static" # 生产部署时收集所有静态文件
# STATICFILES_DIRS  = [
#     BASE_DIR / "static",
# ]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "oss/media"

# 默认主键字段类型
# 为新创建的模型自动添加 BigAutoField 类型的主键字段
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "core_auth.User"

TOKEN_EXPIRE = merge_config("TOKEN_EXPIRE", 7 * 24 * 60 * 60)

# region ******************** Ninja 文档配置 start ******************** #
NINJA_BASE_URL = merge_config("NINJA_BASE_URL", "api")
NINJA_PAGINATION_CLASS = 'core.ninja_extra.base_pagination.AsyncCustomLimitOffsetPagination'
# endregion ****************** Ninja 文档配置 end ********************* #


# region ******************** 日志配置 start ******************** #
LOG_DIR = BASE_DIR / "logs"
LOGGING_BACK_COUNT = merge_config("LOGGING_BACK_COUNT", 10)
LOGGING = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "[%(asctime)s][%(threadName)s:%(thread)d][task_id:%(name)s][%(filename)s:%(lineno)d][%(funcName)s][%(levelname)s] - %(message)s"
                },
                "simple": {
                    "format": "[%(asctime)s][%(filename)s:%(lineno)d][%(funcName)s][%(levelname)s] - %(message)s"
                },
            },
            "handlers": {
                "all": {  # 记录所有日志
                    "level": "DEBUG",
                    "class": "core.logging.multiprocess_time_handler.MultiprocessTimeHandler",
                    "file_path": LOG_DIR,
                    "suffix": "%Y-%m-%d-all",
                    "formatter": "detailed",
                    "backup_count": LOGGING_BACK_COUNT,
                    "encoding": "utf-8",
                },
                "project": {  # 记录项目日志
                    "level": "DEBUG",
                    "class": "core.logging.multiprocess_time_handler.MultiprocessTimeHandler",
                    "file_path": LOG_DIR,
                    "suffix": "%Y-%m-%d-project",
                    "formatter": "detailed",
                    "backup_count": LOGGING_BACK_COUNT,
                    "encoding": "utf-8",
                },
                "error": {  # 只记录错误日志
                    "level": "ERROR",
                    "class": "core.logging.multiprocess_time_handler.MultiprocessTimeHandler",
                    "file_path": LOG_DIR,
                    "suffix": "%Y-%m-%d-error",
                    "formatter": "detailed",
                    "backup_count": LOGGING_BACK_COUNT,
                    "encoding": "utf-8",
                },
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                },
            },
            "loggers": {
                
                "": {
                    "handlers": ["all", "console", "error"],
                    "level": "DEBUG" if DEBUG else "INFO",
                    "propagate": True,
                },
                "project": {
                    "handlers": ["project"],
                    "level": "DEBUG" if DEBUG else "INFO",
                    "propagate": True,
                },
                "django.db.backends": {
                    "handlers": ["console"],
                    "level": "DEBUG" if DEBUG else "ERROR",
                },
            },
        }
# endregion ****************** 日志配置 end ********************* #


# region ******************** simpleui start ******************** #
SIMPLEUI_CONFIG = {
    'system_keep': False,  # 隐藏系统菜单
    # 'menu_display': ['Simpleui', '多级菜单测试', '用户管理', '动态菜单测试'],      # 开启排序和过滤功能, 不填此字段为默认排序和全部显示, 空列表[] 为全部不显示.
    'dynamic': True,    # 设置是否开启动态菜单, 默认为False. 如果开启, 则会在每次用户登陆时动态展示菜单内容
    "menus": []
}
SIMPLEUI_CUSTOM_CSS = 'static/admin/simpleui-x/css/custom.css'
SIMPLEUI_HOME_INFO = False # 去掉右侧多余部分
# endregion ****************** simpleui end ********************* #

# region ******************** 权限 start ******************** #
PERM_PAKC = {
    "STAFF_MANAGE": {
        "name": "员工管理权限",
        "models": {
            "staff.staff": ["add", "change", "view"]
        }
    },
    "FINANCE_MANAGE": {
        "name": "财务管理权限",
        "models": {
            "staff.staffsalary": ["add", "change", "view"]
        }
    },
    "BILL_MANAGE": {
        "name": "票据管理权限",
        "models": {
            "bill.bill": ["add", "change", "view"],
            "bill.billtemplate": ["add", "change", "view"],
        }
    },
    "CLIENT_MANAGE": {
        "name": "客户管理权限",
        "models": {
            "client_mgmt.client": ["add", "change", "view"],
        }
    }
}
# endregion ****************** 权限 end ********************* #
