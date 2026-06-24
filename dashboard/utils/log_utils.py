import logging
from typing import Any, Dict

# 配置日志
logger = logging.getLogger(__name__)


# 通用的日志记录函数
def log_to_console(level: str, message: str, extra: Dict[str, Any] = None) -> None:
    """记录日志到控制台

    Args:
        level: 日志级别 (debug, info, warning, error)
        message: 日志消息
        extra: 额外信息
    """
    if level == "debug":
        logger.debug(message, extra=extra)
    elif level == "info":
        logger.info(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    elif level == "error":
        logger.error(message, extra=extra)
    else:
        logger.info(message, extra=extra)
