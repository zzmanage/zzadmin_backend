"""
自定义异常类模块
提供统一的异常定义，便于异常处理和错误信息传递
"""


class APIException(Exception):
    """基础API异常类，所有自定义异常都应继承此类"""

    def __init__(self, message, code=400):
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationError(APIException):
    """数据验证异常"""

    def __init__(self, message="数据验证失败"):
        super().__init__(message, code=400)


class PermissionDenied(APIException):
    """权限拒绝异常"""

    def __init__(self, message="权限不足"):
        super().__init__(message, code=403)


class NotFoundError(APIException):
    """资源未找到异常"""

    def __init__(self, message="资源不存在"):
        super().__init__(message, code=404)


class AuthenticationError(APIException):
    """认证失败异常"""

    def __init__(self, message="认证失败"):
        super().__init__(message, code=401)


class ServerError(APIException):
    """服务器内部错误异常"""

    def __init__(self, message="服务器内部错误"):
        super().__init__(message, code=500)


class ConflictError(APIException):
    """资源冲突异常"""

    def __init__(self, message="资源冲突"):
        super().__init__(message, code=409)
