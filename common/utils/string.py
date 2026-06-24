"""
字符串工具模块
提供字符串处理相关的工具函数
"""

import re
import random
import string


def is_empty(s):
    """判断字符串是否为空"""
    return s is None or s.strip() == ""


def trim(s):
    """去除两端空白"""
    return s.strip() if s else ""


def truncate(s, max_len, suffix="..."):
    """截断字符串"""
    if len(s) <= max_len:
        return s
    return s[:max_len - len(suffix)] + suffix


def random_string(length=16):
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_number(length=6):
    """生成随机数字"""
    return ''.join(random.choices(string.digits, k=length))


def camel_to_snake(name):
    """驼峰转蛇形"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name, capitalize_first=False):
    """蛇形转驼峰"""
    parts = name.split('_')
    if capitalize_first:
        return ''.join(p.capitalize() for p in parts)
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def mask_phone(phone):
    """脱敏手机号"""
    if len(phone) != 11:
        return phone[:3] + '*' * (len(phone) - 7) + phone[-4:]
    return phone[:3] + '****' + phone[-4:]


def mask_email(email):
    """脱敏邮箱"""
    if '@' not in email:
        return email
    parts = email.split('@')
    username = parts[0]
    if len(username) <= 2:
        username = username[0] + '*' * len(username[1:])
    else:
        username = username[:2] + '*' * (len(username) - 2)
    return f"{username}@{parts[1]}"


def remove_html(s):
    """移除HTML标签"""
    return re.sub(r'<[^>]*>', '', s)


def safe_int(value, default=0):
    """安全转整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """安全转浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
