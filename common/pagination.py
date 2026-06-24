"""
自定义分页器模块
提供统一的分页格式和功能
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """自定义分页器"""

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """返回统一格式的分页响应"""
        return Response({
            "code": 200,
            "message": "操作成功",
            "data": data,
            "success": True,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous()
            }
        })


class LargeResultsSetPagination(PageNumberPagination):
    """大结果集分页器"""

    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500

    def get_paginated_response(self, data):
        return Response({
            "code": 200,
            "message": "操作成功",
            "data": data,
            "success": True,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages
            }
        })


class SmallResultsSetPagination(PageNumberPagination):
    """小结果集分页器"""

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            "code": 200,
            "message": "操作成功",
            "data": data,
            "success": True,
            "pagination": {
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages
            }
        })
