# -*-coding:utf-8 -*-

"""
# File       : md5_cipher.py
# Time       : 2025-07-27 22:52:47
# Author     : lyx
# version    : python 3.11
# Description: MD5 加密
"""
import hashlib
from core.crypto.base_cipher import BaseCipher


class MD5Cipher(BaseCipher):
    """
    支持加盐的 MD5 加密实现（不可逆）
    """

    def __init__(self, salt=None):
        """
        初始化加盐值，默认为空字符串
        :param salt: str | bytes，加盐值
        """
        super(MD5Cipher, self).__init__(key=None)
        if isinstance(salt, str):
            salt = salt.encode("utf-8")
        self.salt = salt or b""

    def encrypt(self, data):
        """
        返回加盐后的 MD5 哈希字符串
        :param data: str 或 bytes
        :return: str
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        md5 = hashlib.md5()
        md5.update(self.salt + data)
        return md5.hexdigest()

    def decrypt(self, data):
        """
        MD5 是不可逆算法，无法解密
        """
        raise NotImplementedError("MD5 是不可逆算法，无法解密")

    @classmethod
    def generate_key(cls, salt_length=16):
        """
        生成一个指定长度的随机盐（可用作“密钥”）
        :param salt_length: 盐的长度
        :return: str
        """
        import os
        return os.urandom(salt_length).hex()
