import logging
from typing import Optional

from captcha.models import CaptchaStore

logger = logging.getLogger(__name__)

def verify_captcha(
    captcha_id: Optional[str] = None, captcha_input: str = None, request=None
) -> bool:
    """验证用户输入的验证码是否正确

    Args:
        captcha_id: 验证码ID，如果使用django-simple-captcha则提供
        captcha_input: 用户输入的验证码字符串
        request: HTTP请求对象（可选）

    Returns:
        bool: 验证结果，True表示验证通过，False表示验证失败
    """
    # 检查必要参数
    if not captcha_id or not captcha_input:
        return False
    
    try:
        # 使用django-simple-captcha提供的验证方法
        is_valid = CaptchaStore.objects.filter(
            hashkey=captcha_id, response=captcha_input.lower()
        ).exists()
        
        # 如果验证成功，删除已使用的验证码
        if is_valid:
            CaptchaStore.objects.filter(hashkey=captcha_id).delete()
        
        return is_valid
    except Exception:
        # 发生异常时返回验证失败
        logger.error(f"验证码验证过程中发生异常: captcha_id={captcha_id}")
        return False