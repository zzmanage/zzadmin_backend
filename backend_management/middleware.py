# 这个文件已经被迁移到 dashboard/middleware/
# 保留此文件以确保向后兼容性
from dashboard.middleware.whitelist_middleware import ApiWhiteListMiddleware
from dashboard.middleware.auth_middleware import (
    AuthenticationMiddleware,
    CORSHeadersMiddleware,
)

# 保留原有的导入路径以确保向后兼容性
__all__ = [
    "ApiWhiteListMiddleware",
    "AuthenticationMiddleware",
    "CORSHeadersMiddleware",
]
