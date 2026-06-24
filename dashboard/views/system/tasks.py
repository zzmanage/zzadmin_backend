import json
import logging
from celery.result import AsyncResult
from django.utils import timezone
from django_celery_beat.models import (
    CrontabSchedule, IntervalSchedule,
    PeriodicTask
)
from rest_framework import permissions, filters, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg

from ...models import TaskLog
from ...serializers import (
    CrontabScheduleSerializer,
    IntervalScheduleSerializer,
    PeriodicTaskSerializer,
    TaskLogSerializer,
    TaskInfoSerializer,
    TaskExecuteSerializer,
    TaskResultSerializer,
)
from ...filters import TaskLogFilter
from ...permissions import AdminPermission
from ..base import BaseViewSet

logger = logging.getLogger(__name__)


class IntervalScheduleViewSet(BaseViewSet):
    """间隔调度视图集

    提供间隔调度的CRUD操作，用于配置任务执行的时间间隔
    """

    queryset = IntervalSchedule.objects.all()
    serializer_class = IntervalScheduleSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        AdminPermission
    ]
    operation_module = "定时任务管理"


class CrontabScheduleViewSet(BaseViewSet):
    """定时调度视图集

    提供定时调度的CRUD操作，用于配置任务执行的定时规则
    """

    queryset = CrontabSchedule.objects.all()
    serializer_class = CrontabScheduleSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        AdminPermission
    ]
    operation_module = "定时任务管理"


class PeriodicTaskViewSet(BaseViewSet):
    """周期性任务视图集

    提供周期性任务的CRUD操作，用于管理定时执行的任务
    """

    queryset = PeriodicTask.objects.all()
    serializer_class = PeriodicTaskSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        AdminPermission
    ]
    operation_module = "定时任务管理"
    filterset_fields = ["name", "task", "enabled", "one_off"]

    @action(detail=True, methods=["post"])
    def enable(self, request, pk=None):
        """启用定时任务"""
        try:
            task = self.get_object()
            task.enabled = True
            task.save()
            logger.info(f"启用定时任务: {task.name}")
            return Response(
                {"status": "success", "message": f"任务 {task.name} 已启用"}
            )
        except Exception as e:
            logger.error(f"启用定时任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        """禁用定时任务"""
        try:
            task = self.get_object()
            task.enabled = False
            task.save()
            logger.info(f"禁用定时任务: {task.name}")
            return Response(
                {"status": "success", "message": f"任务 {task.name} 已禁用"}
            )
        except Exception as e:
            logger.error(f"禁用定时任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """立即执行定时任务"""
        try:
            task = self.get_object()
            logger.info(f"立即执行定时任务: {task.name}")

            args = []
            kwargs = {}
            if task.args:
                args = json.loads(task.args)
            if task.kwargs:
                kwargs = json.loads(task.kwargs)

            task_log = TaskLog.objects.create(
                periodic_task=task,
                task_name=task.task,
                status=TaskLog.STATUS_RUNNING,
                args=task.args or json.dumps([]),
                kwargs=task.kwargs or json.dumps({}),
                start_time=timezone.now(),
                created_by=request.user if request.user.is_authenticated else None,
            )

            from celery import current_app
            try:
                task_result = current_app.send_task(task.task, args=args, kwargs=kwargs)
                if task_result and hasattr(task_result, "id"):
                    task_log.task_id = task_result.id
                    task_log.save()
                    return Response(
                        {
                            "status": "success",
                            "message": f"任务 {task.name} 已开始执行",
                            "task_id": task_result.id,
                        }
                    )
                else:
                    task_log.status = TaskLog.STATUS_FAILED
                    task_log.error_message = "任务发送失败：无法获取任务ID"
                    task_log.save()
                    return Response(
                        {"status": "error", "message": "任务发送失败：无法获取任务ID"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            except Exception as e:
                error_msg = f"任务发送过程中发生错误：{str(e)}"
                logger.error(error_msg)
                task_log.status = TaskLog.STATUS_FAILED
                task_log.error_message = error_msg
                task_log.save()
                return Response(
                    {"status": "error", "message": error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            logger.error(f"执行定时任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaskManagementViewSet(viewsets.ViewSet):
    """任务管理视图集

    提供任务执行状态查询、可用任务列表等功能
    """

    permission_classes = [
        permissions.IsAuthenticated,
        AdminPermission,
    ]

    @action(detail=False, methods=["get"])
    def available_tasks(self, request):
        """获取可用的任务列表"""
        available_tasks = [
            {
                "name": "dashboard.tasks.clean_old_logs",
                "description": "清理旧的操作日志",
                "module": "日志管理",
            },
            {
                "name": "dashboard.tasks.send_reminder_email",
                "description": "发送提醒邮件给用户",
                "module": "用户管理",
            },
            {
                "name": "dashboard.tasks.system_health_check",
                "description": "系统健康检查",
                "module": "系统管理",
            },
            {
                "name": "dashboard.tasks.calculate_statistics",
                "description": "计算系统统计数据",
                "module": "统计管理",
            },
        ]
        serializer = TaskInfoSerializer(available_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def execute_task(self, request):
        """执行指定的任务"""
        serializer = TaskExecuteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                task_name = serializer.validated_data["task_name"]
                args = serializer.validated_data.get("args", [])
                kwargs = serializer.validated_data.get("kwargs", {})

                logger.info(f"执行任务: {task_name}, 参数: {args}, {kwargs}")

                task_log = TaskLog.objects.create(
                    task_name=task_name,
                    status=TaskLog.STATUS_RUNNING,
                    args=json.dumps(args),
                    kwargs=json.dumps(kwargs),
                    start_time=timezone.now(),
                    created_by=request.user if request.user.is_authenticated else None,
                )

                from celery import current_app
                task_result = current_app.send_task(task_name, args=args, kwargs=kwargs)

                task_log.task_id = task_result.id
                task_log.save()

                return Response(
                    {
                        "status": "success",
                        "message": f"任务 {task_name} 已开始执行",
                        "task_id": task_result.id,
                    }
                )
            except Exception as e:
                logger.error(f"执行任务失败: {str(e)}")
                return Response(
                    {"status": "error", "message": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def revoke_task(self, request):
        """撤销正在执行的任务"""
        task_id = request.data.get("task_id")
        if not task_id:
            return Response(
                {"status": "error", "message": "任务ID不能为空"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            task_logs = TaskLog.objects.filter(task_id=task_id)
            if not task_logs.exists():
                return Response(
                    {"status": "error", "message": f"未找到任务ID为{task_id}的记录"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            task_log = task_logs.first()

            if task_log.status != TaskLog.STATUS_RUNNING:
                return Response(
                    {"status": "error", "message": "只有运行中的任务才能被撤销"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = AsyncResult(task_id)
            result.revoke(terminate=True)

            end_time = timezone.now()
            task_log.status = TaskLog.STATUS_REVOKED
            task_log.error_message = "任务被用户手动撤销"
            task_log.end_time = end_time
            task_log.duration = (end_time - task_log.start_time).total_seconds()
            task_log.save()

            logger.info(f"任务已撤销: {task_id}")
            return Response(
                {"status": "success", "message": f"任务{task_id}已成功撤销"}
            )
        except Exception as e:
            logger.error(f"撤销任务失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def task_status(self, request):
        """获取任务执行状态"""
        task_id = request.query_params.get("task_id")
        if not task_id:
            return Response(
                {"status": "error", "message": "任务ID不能为空"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = AsyncResult(task_id)
            status_map = {
                "PENDING": "等待中",
                "STARTED": "执行中",
                "SUCCESS": "成功",
                "FAILURE": "失败",
                "RETRY": "重试",
                "REVOKED": "已撤销",
            }

            task_status = {
                "task_id": task_id,
                "status": status_map.get(result.status, result.status),
                "result": str(result.result) if result.successful() else None,
                "date_done": result.date_done,
                "traceback": str(result.traceback) if result.failed() else None,
            }

            serializer = TaskResultSerializer(task_status)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"查询任务状态失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TaskLogViewSet(BaseViewSet):
    """任务日志视图集

    提供任务日志的查询和管理功能
    """

    queryset = TaskLog.objects.all().order_by("-start_time")
    serializer_class = TaskLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskLogFilter
    search_fields = ['task_name', 'result', 'error_message']
    ordering_fields = ["start_time", "end_time", "duration", "created_at"]
    ordering = ["-start_time"]

    # 操作模块名称
    operation_module = "任务日志管理"

    def create(self, request, *args, **kwargs):
        """禁止创建任务日志，任务日志由系统自动生成"""
        return Response({"error": "任务日志由系统自动生成，不支持手动创建"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, *args, **kwargs):
        """禁止更新任务日志"""
        return Response({"error": "任务日志不支持更新"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        """禁止部分更新任务日志"""
        return Response({"error": "任务日志不支持更新"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        """禁止删除任务日志"""
        return Response({"error": "任务日志不支持删除"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """获取任务日志统计信息"""
        try:
            status_counts = TaskLog.objects.values("status").annotate(
                count=Count("id")
            )

            status_stats = {}
            for item in status_counts:
                status_key = item["status"]
                status_display = dict(TaskLog.STATUS_CHOICES).get(
                    status_key, status_key
                )
                status_stats[status_display] = item["count"]

            avg_duration = TaskLog.objects.filter(duration__isnull=False).aggregate(
                avg=Avg("duration")
            )["avg"]

            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            daily_tasks = (
                TaskLog.objects.filter(start_time__gte=seven_days_ago)
                .extra({"date": "date(start_time)"})
                .values("date")
                .annotate(count=Count("id"))
                .order_by("date")
            )

            return Response(
                {
                    "status_counts": status_stats,
                    "avg_duration": avg_duration if avg_duration else 0,
                    "daily_tasks": list(daily_tasks),
                }
            )
        except Exception as e:
            logger.error(f"获取任务日志统计信息失败: {str(e)}")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )