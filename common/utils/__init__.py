"""
通用工具函数
"""

from .cache import cache_decorator, cache_key
from .date import format_datetime, format_date, parse_datetime, parse_date, now, today
from .date import start_of_day, end_of_day, week_range, month_range, quarter_range, date_range, days_between
from .string import is_empty, trim, truncate, random_string, random_number
from .string import camel_to_snake, snake_to_camel, mask_phone, mask_email, remove_html, safe_int, safe_float
