# -*-coding:utf-8 -*-

"""
# File       : base_cipher.py
# Time       : 2025-07-25 15:54:04
# Author     : lyx
# version    : python 3.11
# Description: 加密解密基类
"""
from abc import ABC, abstractmethod

class BaseCipher(ABC):
    """
    通用加解密基类，定义接口标准
    """

    def __init__(self, key=None):
        self.key = key

    @abstractmethod
    def encrypt(self, data):
        """
        加密方法，需子类实现
        :param data: str / bytes
        :return: 加密后的数据
        """
        pass

    @abstractmethod
    def decrypt(self, data):
        """
        解密方法，需子类实现
        :param data: str / bytes
        :return: 解密后的数据
        """
        pass
    
    
    @classmethod
    @abstractmethod
    def generate_key(cls, *args, **kwargs):
        """
        子类实现：生成秘钥
        返回密钥字符串或对象
        """
        pass

