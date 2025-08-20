from .aes_cipher import AESCipher
from .rsa_cipher import RSACipher
from .md5_cipher import MD5Cipher
from core.conf import settings


aes_cipher = AESCipher(settings.SECRET_KEY)
rsa_cipher = RSACipher(settings.RSA_PUBLIC_KEY, settings.RSA_PRIVATE_KEY)
md5_cipher = MD5Cipher(settings.SECRET_KEY)