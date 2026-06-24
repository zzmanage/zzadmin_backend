"""
日期时间工具模块
提供日期时间处理相关的工具函数
"""

from datetime import datetime, date, timedelta
from dateutil.parser import parse as date_parse
from dateutil.tz import gettz


def format_datetime(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """格式化日期时间"""
    if isinstance(dt, str):
        dt = parse_datetime(dt)
    return dt.strftime(fmt) if dt else ""


def format_date(d, fmt="%Y-%m-%d"):
    """格式化日期"""
    if isinstance(d, str):
        d = parse_date(d)
    return d.strftime(fmt) if d else ""


def parse_datetime(date_str):
    """解析日期时间字符串"""
    if not date_str:
        return None
    try:
        return date_parse(date_str, fuzzy=True)
    except (ValueError, TypeError):
        return None


def parse_date(date_str):
    """解析日期字符串"""
    dt = parse_datetime(date_str)
    return dt.date() if dt else None


def now():
    """获取当前日期时间"""
    return datetime.now(tz=gettz('Asia/Shanghai'))


def today():
    """获取当前日期"""
    return date.today()


def start_of_day(dt=None):
    """获取日期的开始时间 (00:00:00)"""
    if dt is None:
        dt = now()
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day, tzinfo=gettz('Asia/Shanghai'))
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt=None):
    """获取日期的结束时间 (23:59:59)"""
    if dt is None:
        dt = now()
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day, tzinfo=gettz('Asia/Shanghai'))
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def week_range(dt=None):
    """获取周范围 (周一, 周日)"""
    if dt is None:
        dt = today()
    monday = dt - timedelta(days=dt.weekday())
    return monday, monday + timedelta(days=6)


def month_range(dt=None):
    """获取月范围 (月初, 月末)"""
    if dt is None:
        dt = today()
    first = date(dt.year, dt.month, 1)
    if dt.month == 12:
        last = date(dt.year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(dt.year, dt.month + 1, 1) - timedelta(days=1)
    return first, last


def quarter_range(dt=None):
    """获取季度范围"""
    if dt is None:
        dt = today()
    quarter = (dt.month - 1) // 3
    start_month = quarter * 3 + 1
    first = date(dt.year, start_month, 1)
    if start_month == 12:
        last = date(dt.year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(dt.year, start_month + 3, 1) - timedelta(days=1)
    return first, last


def date_range(days=7):
    """获取过去N天的范围"""
    end = today()
    start = end - timedelta(days=days - 1)
    return start, end


def days_between(start_date, end_date):
    """计算天数差"""
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    return (end_date - start_date).days
