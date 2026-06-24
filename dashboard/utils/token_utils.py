"""
Token工具模块
提供token生成和验证功能
"""
import hashlib
import random
import string
from datetime import datetime, timedelta


class TokenGenerator:
    """Token生成器"""

    def __init__(self):
        self.secret_key = "dashboard_secret_key_2024"

    def generate_token(self, user_id):
        """
        生成token
        :param user_id: 用户ID
        :return: 生成的token字符串
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        raw = f"{user_id}{timestamp}{random_str}{self.secret_key}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        return token

    def generate_refresh_token(self, user):
        """
        生成刷新token
        :param user: 用户对象
        :return: 生成的refresh token字符串
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        user_id = user.id if hasattr(user, 'id') else user
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        raw = f"refresh_{user_id}{timestamp}{random_str}{self.secret_key}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        return token

    def generate_verify_token(self, user_id, expire_minutes=30):
        """
        生成验证token（带过期时间）
        :param user_id: 用户ID
        :param expire_minutes: 过期时间（分钟）
        :return: 生成的token字符串
        """
        expire_time = (datetime.now() + timedelta(minutes=expire_minutes)).strftime(
            "%Y%m%d%H%M%S"
        )
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        raw = f"{user_id}{expire_time}{random_str}{self.secret_key}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        return token, expire_time

    def validate_token(self, token, user_id, expire_time):
        """
        验证token
        :param token: 需要验证的token
        :param user_id: 用户ID
        :param expire_time: 过期时间戳
        :return: 是否有效
        """
        # 检查是否过期
        if datetime.now() > datetime.strptime(expire_time, "%Y%m%d%H%M%S"):
            return False

        # 重新计算token进行比对
        random_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))
        raw = f"{user_id}{expire_time}{random_str}{self.secret_key}"
        expected_token = hashlib.sha256(raw.encode()).hexdigest()

        return token == expected_token