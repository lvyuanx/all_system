# -*-coding:utf-8 -*-

"""
# File       : aes_cipher.py
# Time       : 2025-07-25 16:05:49
# Author     : lyx
# version    : python 3.11
# Description: AES加解密
"""
# crypto/aes_cipher.py

from Crypto.Random import get_random_bytes
import base64
from .base_cipher import BaseCipher
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib

class AESCipher(BaseCipher):
    def __init__(self, key, iv=None):
        super(AESCipher, self).__init__(key)
        self.bs = AES.block_size
        self.key = hashlib.md5(key.encode()).digest()  # 16字节
        self.iv = iv.encode() if iv else self.key[:16]

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode()
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = cipher.encrypt(pad(data, self.bs))
        return base64.b64encode(encrypted).decode()

    def decrypt(self, enc_data):
        raw = base64.b64decode(enc_data)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted = unpad(cipher.decrypt(raw), self.bs)
        return decrypted.decode()

    @classmethod
    def generate_key(cls, length=16):
        """
        生成随机 AES 密钥（默认 16 字节）
        返回 base64 编码字符串
        """
        key = get_random_bytes(length)
        return base64.b64encode(key).decode()
