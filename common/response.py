"""
统一响应格式模块
提供统一的API响应封装，确保所有API返回格式一致
"""

from rest_framework.response import Response


class APIResponse:
    """统一API响应类"""

    @staticmethod
    def success(data=None, message="操作成功", code=200):
        """成功响应"""
        return Response({
            "code": code,
            "message": message,
            "data": data,
            "success": True
        })

    @staticmethod
    def error(message="操作失败", code=400, data=None):
        """失败响应"""
        return Response({
            "code": code,
            "message": message,
            "data": data,
            "success": False
        })

    @staticmethod
    def paginated(data, total, page=1, page_size=10, message="操作成功"):
        """分页响应"""
        return Response({
            "code": 200,
            "message": message,
            "data": data,
            "success": True,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        })
