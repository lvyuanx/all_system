# 文档相关配置
NINJA_BASE_URL = "api/"  # ninja跟路径

# 拦截器配置
TOKEN_TAG = "X-Authorization"   # token标记名称
TOKEN_ORIGIN = "cookie"         # token来源
TOKEN_EXPIRE = 60 * 60 * 24 * 7 # token过期时间

DEFAULT_AVATAR = "system/user_default.png"
DEFAULT_IMAGE = "system/image_default.png"
DEFAULT_PASSWORD = "pbkdf2_sha256$1000000$wnP11gGVJKY6iQU9DYhk8T$oy5s1ER1KTMJucthUHRE9FjI6YwG2PVug2kyKTLRB3I=" # 默认密码
# 密钥配置
RSA_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2OfIs63GS25nZei8ege6
tyVXIsShOLFkl/HXfiuTt+UsnRSwsF7ng3q4sEhpqLk+kt+pjNNxU493/Y75rM+I
JWVjoglglAJqWnz1zOyeqLiXr1a7CvWuh3w4sQGoRUtqzD99KhwLxYQCXvNj1ciZ
0X9J0qnl8IcoaDyazxVOPPNLL7qwS96dNZZYJQJ0oPzJc86sk/CyetjzNbJTdDAd
6FnpjK8khwZQ+peyJ847hUshKeQtzCCHUoZDRRF+7X5sKI9+V9RJ70QgCIVnLelc
9qBLfVNbXWlYaI09zp9REt2BEzwa/p4ymkntkCwb2ZrfudHvZi/E1/vAKr56oDAW
ewIDAQAB
-----END PUBLIC KEY-----"""
RSA_PRIVATE_KEY  = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA2OfIs63GS25nZei8ege6tyVXIsShOLFkl/HXfiuTt+UsnRSw
sF7ng3q4sEhpqLk+kt+pjNNxU493/Y75rM+IJWVjoglglAJqWnz1zOyeqLiXr1a7
CvWuh3w4sQGoRUtqzD99KhwLxYQCXvNj1ciZ0X9J0qnl8IcoaDyazxVOPPNLL7qw
S96dNZZYJQJ0oPzJc86sk/CyetjzNbJTdDAd6FnpjK8khwZQ+peyJ847hUshKeQt
zCCHUoZDRRF+7X5sKI9+V9RJ70QgCIVnLelc9qBLfVNbXWlYaI09zp9REt2BEzwa
/p4ymkntkCwb2ZrfudHvZi/E1/vAKr56oDAWewIDAQABAoIBAArPBt3u5rbzKhN8
+1XSNS66A9NhHKH+zQMS84JMP52ZV2JlTPMgN5JotvPDfmhnASqmgWqmgSFnc9Sr
bEVKFJm9QxX1a6rUfmJCxqjokNtz7DMgZxlO6g/CulYWJA5LIzSvl6TvWT+fEJ/7
EI2I5CL5bQwimHYmj6mDsGwDWGIj3thdFrUX3v4yuPeP3uogCPqti0UahGRbVSbZ
MKybiP/DMAnocYDRHdnaJPgokAoV541Gt+ai4tL2HLlkkapDX4M4kLEs/OmAgo1c
qp0ODFt/O84qr6Iuf9CqgPicVi3iTzEZ68S/P2CCSEZyu3BHQVSmMdmODvNCmY69
pd9nq/ECgYEA3yntcrG42e47dtfYjwuEFDvnOZpvu8rTyUxSjsC40jjHOM0daSFU
hWZMIdgSCILUmICWGml2B6vPYd8Ygvj/AqxCvlONUAcGKDyrd7btWJymKDYBssxw
YabMVllz4DNTprI6/Ooi0DLIIOZQf40Q6cfJXIP4/OHOL4Qw17jzLHMCgYEA+NIe
JbX6HApADvKzZjgZeUokqJ6nJZbZCdIs/p1ICvH8Bz/+dJunxZvKGJ7RhWBISCpD
fr/W1Iq4GLtsjh112cDmJZS9hgbb1mGyVeyb3Xmpi/lIxOv8heFxwrNKq+nc9EcM
joO+rcEholbgJncQoX9fh6GNC/5FhOGgSqpZs9kCgYEAjfRFrqeORlJcUQSMJLHW
mmhgdSvf1zz16x45hcThzBeB4ofXJYCmGxUvaHfhQLi4MynYUYS0J70Kdd9L4EQz
MqgQ7LCJO1a8e+vbxpL991ft+bYg7nNNKVDIukS8iOkdVPQawbbN3lHvK75Vhk1d
bNhBJjBsua+JUIBt8UscpDECgYBU3satsj6XZd+nuZz7ltMJjgKnCUaWCbgKI4h5
aIh0Q0nl5ywR9i3pt1Pdxf5NciP1iYTwLNtIL/DPbs5+Qwo5thRKaUuj9Z7ypuw/
Zq9bge4U8nihwqSlvdohwSoNLX3STJG54rIdbizcxKk8NYyUqW+aQb5sgtSPmK4m
CakDMQKBgBcp8K8p03xddrpfMoUvVZhJZ/p5INXfj1feexCN4wWDhpQ9cW7l8NYr
V2rmi5NOrAmLMZhElJLvZbVI/aKKFELr1okwjYT3FAAYOB1FZsPYM51Us6MdtBpV
RNwhSHuwJpbpie14O0WgSDluHGPfrQxXsUYTnRqRoRcgT7p76lf9
-----END RSA PRIVATE KEY-----"""

# region ******************** Ninja start ******************** #
NINJA_TITLE = "Ninja在线文档"
NINJA_DESCRIPTION = """
**基于Swagger的在线文档**

一款为Django5.0打造的高性能Web框架, 支持在线调试。
"""
NINJA_VERSION = "0.1.0"

_NINJAT_EXCEPTION_HANDLERS = {
    "core.exceptions.base_exceptions.BaseException": "core.ninja_extra.exception_handlers:base_exception_handler",
    "Exception": "core.ninja_extra.exception_handlers:finally_exception_handler",
}  # 内部异常处理
NINJAT_EXCEPTION_HANDLERS = {}  # 自定义异常处理
# endregion ****************** Ninja end ********************* #

# region ******************** 权限 start ******************** #
_PERM_PAKC = {
    "USER_MANAGE": {
        "name": "用户管理权限",
        "models": {
            "core_auth.user": ["add", "change", "view"],
            "auth.group": ["view"],
        }
    }
}
# endregion ****************** 权限 end ********************* #