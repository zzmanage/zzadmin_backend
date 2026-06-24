# -*- coding: utf-8 -*-
"""
通用过滤混入类，提供基于查询参数的通用过滤功能
"""
import logging
from django.db.models import QuerySet

# 配置日志
logger = logging.getLogger(__name__)


class FilterMixin:
    """通用过滤混入类

    提供基于查询参数的通用过滤功能，可以被所有ViewSet复用
    支持字符串、布尔值、整数、日期等类型的过滤
    """

    def get_queryset(self):
        """获取查询集，支持基于查询参数的过滤

        Returns:
            QuerySet: 过滤后的查询集
        """
        # 获取基础查询集
        queryset = super().get_queryset()

        # 获取模型类
        model_class = queryset.model

        # 遍历所有查询参数
        for param_name, param_value in self.request.query_params.items():
            # 跳过分页参数和空值参数
            if param_name in ["page", "page_size", "format"] or param_value == '':
                continue

            # 检查参数是否是模型的字段
            if hasattr(model_class, param_name):
                field_type = model_class._meta.get_field(param_name)

                # 根据字段类型处理参数值
                try:
                    # 处理布尔字段
                    if field_type.get_internal_type() == "BooleanField":
                        bool_value = param_value.lower() == "true" or param_value == "1"
                        queryset = queryset.filter(**{param_name: bool_value})
                    # 处理整数字段
                    elif field_type.get_internal_type() in [
                        "IntegerField",
                        "ForeignKey",
                        "OneToOneField",
                    ]:
                        # 处理空值情况
                        if param_value.lower() in ["null", "none"]:
                            queryset = queryset.filter(
                                **{f"{param_name}__isnull": True}
                            )
                        else:
                            try:
                                int_value = int(param_value)
                                queryset = queryset.filter(**{param_name: int_value})
                            except ValueError:
                                # 无法转换为整数，跳过此参数
                                pass
                    # 处理日期/时间字段
                    elif field_type.get_internal_type() in [
                        "DateField",
                        "DateTimeField",
                    ]:
                        # 这里可以根据需要添加日期格式化逻辑
                        try:
                            # 简单处理，假设前端传来的日期格式正确
                            queryset = queryset.filter(**{param_name: param_value})
                        except BaseException:
                            # 日期格式错误，跳过此参数
                            pass
                    # 默认使用包含查询（针对字符串字段）
                    else:
                        queryset = queryset.filter(
                            **{f"{param_name}__icontains": param_value}
                        )
                except Exception as e:
                    # 捕获所有异常，确保即使参数处理失败也不会影响主流程
                    logger.warning(f"Failed to filter by {param_name}: {str(e)}")

        return queryset