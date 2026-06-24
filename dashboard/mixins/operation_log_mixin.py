# -*- coding: utf-8 -*-
"""
操作日志混入类，提供创建、更新、删除操作的日志记录功能
"""
import logging
from typing import Any, Dict

from django.db.models import Model

from dashboard.models import OperationLog

# 配置日志
logger = logging.getLogger(__name__)


class OperationLogMixin:
    """操作日志混入类

    提供创建、更新、删除操作的日志记录功能
    用于减少各ViewSet中的代码重复
    """

    def _get_operation_message(self, action: str) -> str:
        """根据操作类型获取操作描述

        Args:
            action: 操作类型 (create, update, delete)

        Returns:
            str: 操作描述
        """
        operation_map = {"create": "创建", "update": "更新", "delete": "删除"}
        return operation_map.get(action.lower(), action)

    def _get_module_name(self) -> str:
        """获取模块名称

        Returns:
            str: 模块名称
        """
        # 从序列化器类名中提取模型名称
        if hasattr(self, "serializer_class"):
            model_name = self.serializer_class.__name__.replace("Serializer", "")
            return f"{model_name}模块"
        return "未知模块"

    def _get_model_id(self, instance: Any) -> int:
        """获取模型实例的ID

        Args:
            instance: 模型实例

        Returns:
            int: 模型ID
        """
        return getattr(instance, "id", None)

    def _get_model_name(self, instance: Any) -> str:
        """获取模型名称

        Args:
            instance: 模型实例

        Returns:
            str: 模型名称
        """
        return instance.__class__.__name__

    def _get_instance_name(self, instance: Any) -> str:
        """获取实例的名称或标识

        Args:
            instance: 模型实例

        Returns:
            str: 实例名称
        """
        # 尝试获取常用的名称字段
        for field_name in ["name", "username", "title", "label"]:
            if hasattr(instance, field_name):
                return str(getattr(instance, field_name))
        return str(instance)

    def _log_operation(
        self, request, action: str, instance: Any, old_data: Dict[str, Any] = None
    ) -> None:
        """记录操作日志

        Args:
            request: HTTP请求对象
            action: 操作类型
            instance: 模型实例
            old_data: 旧数据（用于更新操作）
        """
        try:
            # 获取操作信息
            operation = self._get_operation_message(action)
            module = self._get_module_name()
            model_name = self._get_model_name(instance)
            model_id = self._get_model_id(instance)

            # 构建详情信息
            if action == "update" and old_data:
                # 更新操作，显示变更
                instance_name = self._get_instance_name(instance)
                old_name = old_data.get("name", "未知")
                details = f"{operation}{model_name}: {old_name} -> {instance_name}"
            else:
                # 创建或删除操作
                instance_name = self._get_instance_name(instance)
                details = f"{operation}{model_name}: {instance_name}"

            # 记录日志
            OperationLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                operation=operation,
                action=action,
                module=module,
                model_name=model_name,
                model_id=model_id,
                details=details,
                ip_address=request.META.get("REMOTE_ADDR", "unknown"),
            )

            # 记录到系统日志
            logger.info(
                f"Operation logged: {details} by user "
                f"{request.user.username if request.user.is_authenticated else 'anonymous'}"
            )

        except Exception as e:
            # 记录日志时发生异常不应影响主流程
            logger.error(f"Failed to log operation: {str(e)}", exc_info=True)

    def perform_create(self, serializer):
        """创建实例时记录日志

        重写ModelViewSet的perform_create方法
        """
        instance = serializer.save()
        self._log_operation(self.request, "create", instance)

    def perform_update(self, serializer):
        """更新实例时记录日志

        重写ModelViewSet的perform_update方法
        """
        instance = self.get_object()
        old_data = {
            "name": getattr(instance, "name", None),
            # 可以添加其他需要记录的字段
        }
        updated_instance = serializer.save()
        self._log_operation(self.request, "update", updated_instance, old_data)

    def perform_destroy(self, instance):
        """删除实例时记录日志

        重写ModelViewSet的perform_destroy方法
        """
        self._log_operation(self.request, "delete", instance)
        instance.delete()