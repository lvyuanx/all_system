# -*-coding:utf-8 -*-

"""
# File       : rsa_cipher.py
# Time       : 2025-07-25 16:06:35
# Author     : lyx
# version    : python 3.11
# Description: RSA非对称加解密
"""

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
from .base_cipher import BaseCipher

class RSACipher(BaseCipher):
    def __init__(self, public_key=None, private_key=None):
        super(RSACipher, self).__init__()
        self.public_key = RSA.import_key(public_key) if public_key else None
        self.private_key = RSA.import_key(private_key) if private_key else None

    def encrypt(self, data):
        if not self.public_key:
            raise ValueError("Public key is required for encryption")
        if isinstance(data, str):
            data = data.encode()
        cipher = PKCS1_OAEP.new(self.public_key)
        return base64.b64encode(cipher.encrypt(data)).decode()

    def decrypt(self, enc_data):
        if not self.private_key:
            raise ValueError("Private key is required for decryption")
        raw = base64.b64decode(enc_data)
        cipher = PKCS1_OAEP.new(self.private_key)
        return cipher.decrypt(raw).decode()

    @classmethod
    def generate_key(cls, key_size=2048):
        """
        生成 RSA 公私钥对
        :return: dict with 'private_key', 'public_key'
        """
        key = RSA.generate(key_size)
        private_key = key.export_key().decode()
        public_key = key.publickey().export_key().decode()
        return {
            'private_key': private_key,
            'public_key': public_key
        }
