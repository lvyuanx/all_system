#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Filename: time_util.py
Author: lvyuanxiang
Date: 2025/01/03 15:33:13
Description: 时间相关工具, 默认时区：Asia/Shanghai
"""
from datetime import date, datetime
import datetime as dt
import pytz


default_tz = pytz.timezone('Asia/Shanghai')
date_fromat = "%Y-%m-%d"
time_format = "%H:%M:%S"
datetime_format = f"{date_fromat} {time_format}"
default_format = datetime_format

def now(tz: pytz.timezone = default_tz) -> datetime:
    """获取当前时间

    :param tz: 时区
    :return: 当前时间
    """
    return datetime.now(tz)

def datetime_to_str(datetime: datetime, format: str = default_format, tz: pytz.timezone = default_tz) -> str:
    """将datetime转换为字符串
    
    :param datetime: datetime对象
    :param format: 格式
    :param tz: 时区
    :return: 字符串
    """
    return datetime.astimezone(tz).strftime(format)

def str_to_datetime(str: str, format: str = default_format, tz: pytz.timezone = default_tz) -> datetime:
    """将字符串转换为datetime
    
    :param str: 字符串
    :param format: 格式
    :param tz: 时区
    :return: datetime对象
    """
    return datetime.strptime(str, format).replace(tzinfo=tz)

def datetime_to_timestamp(datetime: datetime, tz: pytz.timezone = default_tz) -> int:
    """将datetime转换为时间戳

    :param datetime: datetime对象
    :param tz: 时区
    :return: 时间戳
    """
    return int(datetime.astimezone(tz).timestamp())

def timestamp_to_datetime(timestamp: int, tz: pytz.timezone = default_tz) -> datetime:
    """将时间戳转换为datetime

    :param timestamp: 时间戳
    :param tz: 时区
    :return: datetime对象
    """
    return datetime.fromtimestamp(timestamp, tz)

def now_str(format: str = default_format, tz: pytz.timezone = default_tz):
    """获取当前时间字符串
    
    :param format: 格式
    :param tz: 时区
    :return: 当前时间字符串
    """
    return datetime_to_str(now(tz), format, tz)

def now_timestamp(tz: pytz.timezone = default_tz) -> int:
    """获取当前时间戳
    
    :param tz: 时区
    :return: 当前时间戳
    """
    return datetime_to_timestamp(now(tz), tz)

def in_range(datetime: datetime, start: datetime, end: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否在范围内
    
    :param datetime: 要判断的时间
    :param start: 开始时间
    :param end: 结束时间
    :param tz: 时区
    :return: 是否在范围内
    """
    return start.astimezone(tz) <= datetime.astimezone(tz) <= end.astimezone(tz)

def is_today(datetime: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否是今天
    
    :param datetime: 要判断的时间
    :param tz: 时区
    :return: 是否是今天
    """
    return now(tz).date() == datetime.astimezone(tz).date()

def is_yesterday(datetime: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否是昨天
    
    :param datetime: 要判断的时间
    :param tz: 时区
    :return: 是否是昨天
    """
    return now(tz).date() - datetime.astimezone(tz).date() == datetime.timedelta(days=1)

def is_tomorrow(datetime: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否是明天
    
    :param datetime: 要判断的时间
    :param tz: 时区
    :return: 是否是明天
    """
    return now(tz).date() - datetime.astimezone(tz).date() == datetime.timedelta(days=-1)

def is_weekend(datetime: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否是周末
    
    :param datetime: 要判断的时间
    :param tz: 时区
    :return: 是否是周末
    """
    return datetime.astimezone(tz).weekday() in [5, 6]


def is_greater_than(datetime: datetime, other: datetime, tz: pytz.timezone = default_tz) -> bool:
    """判断时间是否大于另一个时间
    
    :param datetime: 要判断的时间
    :param other: 另一个时间
    :param tz: 时区
    :return: 是否大于另一个时间
    """
    return datetime.astimezone(tz) > other.astimezone(tz)

def change_tz(datetime: datetime, tz: pytz.timezone = default_tz) -> datetime:
    """更改时区

    :param datetime: 被更改的时间
    :param tz: 时区
    """
    return datetime.astimezone(tz)

def datetime_to_date(datetime: datetime, tz: pytz.timezone = default_tz) -> date:
    """将datetime转换为日期
    
    :param datetime: datetime对象
    :param tz: 时区
    :return: 日期
    """
    return datetime.astimezone(tz).date()

def date_to_datetime(date: date, tz: pytz.timezone = default_tz)-> datetime:
    """将日期转换为datetime
    
    :param date: 日期
    :param tz: 时区
    :return: datetime对象
    """
    return datetime.combine(date, datetime.min.time()).replace(tzinfo=tz)

def add_days(date: datetime, day: int, tz: pytz.timezone = default_tz) -> datetime:
    """将日期增加天数
    
    :param datetime: 日期
    :param day: 天数
    :param tz: 时区
    :return: 增加天数后的日期
    """
    return date.astimezone(tz) + dt.timedelta(days=day)

def change_time(datetime: datetime, time: str, tz: pytz.timezone = default_tz):
    """更改时间
    
    :param datetime: 要更改的时间
    :param time: 时间
    :param tz: 时区
    :return: 更改后的时间
    """
    return datetime.astimezone(tz).replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]), second=0)

def add_time(datetime: datetime, time: str, tz: pytz.timezone = default_tz):
    """增加时间
    
    :param datetime: 要增加的时间
    :param time: 时间
    :param tz: 时区
    :return: 增加后的时间
    """
    return datetime.astimezone(tz) + dt.timedelta(hours=int(time.split(':')[0]), minutes=int(time.split(':')[1]))

def add_seconds(datetime: datetime, second: int, tz: pytz.timezone = default_tz) -> datetime:
    """增加秒数
    
    :param datetime: 要增加的时间
    :param second: 秒数
    :param tz: 时区
    :return: 增加后的时间
    """
    return datetime.astimezone(tz) + dt.timedelta(seconds=second)



