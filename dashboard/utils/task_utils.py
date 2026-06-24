# -*- coding: utf-8 -*-
"""
任务工具模块，提供任务日志记录装饰器、参数处理、定时计划创建等功能
"""
import functools
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, IntervalSchedule

from dashboard.models import TaskLog

# 配置日志记录器
logger = logging.getLogger(__name__)

# 线程本地存储，用于存储当前任务的上下文信息
_thread_local = threading.local()

# 缓存相关配置
TASK_LOG_CACHE_PREFIX = "task_log_"
TASK_LOG_CACHE_TIMEOUT = 60 * 10  # 10分钟

# 线程池配置
ASYNC_EXECUTOR = ThreadPoolExecutor(
    max_workers=getattr(settings, "CELERY_SIGNAL_WORKERS", 4)
)

# 批量处理配置
BATCH_UPDATE_INTERVAL = 0.5  # 秒
_batched_updates = {}
_batch_lock = threading.Lock()
_last_batch_processed = 0


def safe_json_serialize(data):
    """
    安全地将数据序列化为JSON字符串，处理不可序列化的对象

    Args:
        data: 需要序列化的数据

    Returns:
        str: 序列化后的JSON字符串，如果序列化失败则返回错误信息
    """
    try:
        return json.dumps(data, default=lambda o: str(o))
    except Exception as e:
        logger.error(f"JSON序列化失败: {str(e)}")
        return f"<序列化错误: {str(e)}>"


def task_with_logging(func):
    """
    任务日志记录装饰器
    自动处理任务日志的创建、状态更新、进度跟踪等通用逻辑

    Args:
        func: 被装饰的Celery任务函数

    Returns:
        包装后的函数
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        task_log = None
        start_time = timezone.now()
        result_message = ""
        error_message = ""
        is_success = True
        task_name = func.__name__

        try:
            # 获取任务ID
            task_id = func.request.id if hasattr(func, "request") else None

            # 查找或创建任务日志
            if task_id:
                task_logs = TaskLog.objects.filter(task_id=task_id)
                if task_logs.exists():
                    task_log = task_logs.first()

            if not task_log:
                task_log = TaskLog.objects.create(
                    task_name=task_name,
                    task_id=task_id,
                    status=TaskLog.STATUS_RUNNING,
                    args=safe_json_serialize(args),
                    kwargs=safe_json_serialize(kwargs),
                    start_time=start_time,
                    progress=0,  # 初始化进度为0
                )
                logger.info(
                    f"创建任务日志: {task_name} (ID: {task_id})"
                    if task_id
                    else f"创建任务日志: {task_name}"
                )
            else:
                task_log.status = TaskLog.STATUS_RUNNING
                task_log.start_time = start_time
                task_log.progress = 0  # 重置进度
                task_log.save()
                logger.info(
                    f"更新任务状态为运行中: {task_name} (ID: {task_id})"
                    if task_id
                    else f"更新任务状态为运行中: {task_name}"
                )

            # 存储任务日志到线程本地存储，供update_task_progress使用
            _thread_local.task_log = task_log

            # 执行原始任务函数
            result_message = func(*args, **kwargs)

        except Exception as e:
            error_message = str(e)
            logger.error(f"任务执行失败: {task_name} - {error_message}")
            is_success = False
        finally:
            # 在finally块中更新任务日志，确保无论是否有异常都会执行
            if task_log:
                end_time = timezone.now()
                task_log.end_time = end_time
                task_log.duration = (end_time - start_time).total_seconds()

                if is_success:
                    task_log.status = TaskLog.STATUS_SUCCESS
                    task_log.result = str(result_message)
                    task_log.progress = 100  # 任务成功完成，进度设为100%
                else:
                    task_log.status = TaskLog.STATUS_FAILED
                    task_log.error_message = error_message

                try:
                    # 使用原子操作保存，避免事务回滚
                    task_log.save()
                    logger.info(
                        f"更新任务日志完成: {task_name} - 状态: {'成功' if is_success else '失败'}"
                    )
                except Exception as save_error:
                    logger.error(f"保存任务日志失败: {task_name} - {str(save_error)}")

            # 清理线程本地存储
            if hasattr(_thread_local, "task_log"):
                delattr(_thread_local, "task_log")

            # 如果有异常，这里可以选择是否重新抛出
            if not is_success and error_message:
                # 注意：如果继续抛出异常，可能仍会导致事务回滚
                # 可以根据实际需求决定是否抛出
                # raise Exception(error_message)
                return f"任务执行失败: {error_message}"

        return result_message

    return wrapper


def update_task_progress(progress, message=None):
    """
    更新任务进度

    Args:
        progress: 任务进度百分比 (0-100)
        message: 可选的进度消息
    """
    try:
        # 确保进度在有效范围内
        progress = max(0, min(100, progress))

        # 检查线程本地存储中是否有任务日志，并且是TaskLog类型
        if hasattr(_thread_local, "task_log"):
            task_log = _thread_local.task_log
            # 确保task_log有progress属性（是TaskLog实例）
            if hasattr(task_log, "progress"):
                task_log.progress = progress
                if message:
                    task_log.result = message  # 使用result字段临时存储进度消息
                task_log.save(
                    update_fields=["progress", "result"] if message else ["progress"]
                )
                logger.debug(
                    (f"更新任务进度: {task_log.task_name} - {progress}%"
                     f"{f' ({message})' if message else ''}")
                )
            else:
                logger.warning(
                    f"线程本地存储中的task_log没有progress属性: {type(task_log)}"
                )
    except Exception as e:
        logger.error(f"更新任务进度失败: {str(e)}")


def _get_task_log_from_cache(task_id):
    """
    从缓存获取任务日志，如果缓存不存在则从数据库获取并缓存

    Args:
        task_id: 任务ID

    Returns:
        TaskLog对象或None
    """
    cache_key = f"{TASK_LOG_CACHE_PREFIX}{task_id}"
    task_log = cache.get(cache_key)

    if not task_log:
        try:
            task_log = TaskLog.objects.filter(task_id=task_id).first()
            if task_log:
                cache.set(cache_key, task_log, TASK_LOG_CACHE_TIMEOUT)
        except Exception as e:
            logger.error(f"从数据库获取任务日志失败: {str(e)}")

    return task_log


def get_task_parameters(task_name: str) -> Dict[str, Any]:
    """
    获取指定任务的参数配置信息
    用于前端动态生成参数表单

    Args:
        task_name: 任务名称

    Returns:
        Dict: 包含任务参数配置的字典
    """
    # 从PeriodicTask中获取任务参数信息
    import json

    from django_celery_beat.models import PeriodicTask

    try:
        # 查找使用该任务的PeriodicTask对象
        periodic_task = PeriodicTask.objects.filter(task=task_name).first()

        if periodic_task and periodic_task.kwargs:
            try:
                # 解析kwargs JSON字符串为字典
                kwargs = json.loads(periodic_task.kwargs)

                # 构建参数配置信息
                params_info = {
                    "description": periodic_task.description or "未知任务",
                    "params": [],
                }

                # 根据kwargs的键值对生成参数配置
                for key, value in kwargs.items():
                    param_type = "string"
                    if isinstance(value, int) or isinstance(value, float):
                        param_type = "number"
                    elif isinstance(value, bool):
                        param_type = "boolean"
                    elif isinstance(value, list):
                        param_type = "array"
                    elif isinstance(value, dict):
                        param_type = "object"

                    param_config = {
                        "name": key,
                        "type": param_type,
                        "default": value,
                        "description": f"参数{key}",
                        "required": False,  # 默认都不是必填参数，可以根据实际需求调整
                    }
                    params_info["params"].append(param_config)

                return params_info
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回默认信息
                pass
    except Exception as e:
        # 捕获任何异常，确保函数不会失败
        logger.error(f"从PeriodicTask获取任务参数信息失败: {str(e)}")

    # 如果找不到对应的PeriodicTask或出现其他问题，使用默认的任务参数配置映射
    task_params_map = {
        "dashboard.tasks.clean_old_logs": {
            "description": "清理指定天数前的操作日志",
            "params": [
                {
                    "name": "days",
                    "type": "number",
                    "default": 30,
                    "description": "保留最近多少天的日志",
                    "required": False,
                }
            ],
        },
        "dashboard.tasks.send_reminder_email": {
            "description": "发送提醒邮件给指定用户",
            "params": [
                {
                    "name": "user_id",
                    "type": "number",
                    "description": "用户ID",
                    "required": True,
                },
                {
                    "name": "message",
                    "type": "string",
                    "description": "提醒消息内容",
                    "required": True,
                },
            ],
        },
        "dashboard.tasks.system_health_check": {
            "description": "系统健康检查任务",
            "params": [],
        },
        "dashboard.tasks.calculate_statistics": {
            "description": "计算系统统计数据",
            "params": [
                {
                    "name": "days",
                    "type": "number",
                    "default": 7,
                    "description": "统计最近多少天的数据",
                    "required": False,
                }
            ],
        },
    }

    return task_params_map.get(task_name, {"description": "未知任务", "params": []})


def validate_task_parameters(
    task_name: str, args: Optional[List] = None, kwargs: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    验证任务参数是否符合要求

    Args:
        task_name: 任务名称
        args: 位置参数列表
        kwargs: 关键字参数字典

    Returns:
        Dict: 包含验证结果和错误信息的字典
    """
    result = {"valid": True, "errors": []}

    task_info = get_task_parameters(task_name)

    # 检查必填的关键字参数
    required_params = [
        p["name"] for p in task_info["params"] if p.get("required", False)
    ]

    if kwargs:
        for param in required_params:
            if param not in kwargs:
                result["valid"] = False
                result["errors"].append(f"缺少必填参数: {param}")
    elif required_params:
        result["valid"] = False
        result["errors"].append(f"缺少必填参数: {', '.join(required_params)}")

    # 简单的类型检查
    if kwargs:
        for param_config in task_info["params"]:
            param_name = param_config["name"]
            param_type = param_config["type"]

            if param_name in kwargs:
                value = kwargs[param_name]
                if param_type == "number" and not isinstance(value, (int, float)):
                    try:
                        # 尝试转换字符串为数字
                        float(value)
                    except (ValueError, TypeError):
                        result["valid"] = False
                        result["errors"].append(f"参数 {param_name} 应该是数字类型")

    return result


def create_schedule(schedule_type: str, schedule_data: Dict) -> Optional[Any]:
    """
    创建定时计划

    Args:
        schedule_type: 计划类型，'interval'或'crontab'
        schedule_data: 计划数据

    Returns:
        计划实例或None
    """
    try:
        if schedule_type == "interval":
            # 创建间隔计划
            interval, _ = IntervalSchedule.objects.get_or_create(
                every=schedule_data.get("every", 1),
                period=schedule_data.get("period", "minutes"),
            )
            return interval
        elif schedule_type == "crontab":
            # 创建Crontab计划
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=schedule_data.get("minute", "*"),
                hour=schedule_data.get("hour", "*"),
                day_of_week=schedule_data.get("day_of_week", "*"),
                day_of_month=schedule_data.get("day_of_month", "*"),
                month_of_year=schedule_data.get("month_of_year", "*"),
            )
            return crontab
        return None
    except Exception as e:
        logger.error(f"创建计划失败: {str(e)}")
        return None


def _get_task_log_from_cache(task_id):
    """
    从缓存获取任务日志，如果缓存不存在则从数据库获取并缓存
    """
    cache_key = f"{TASK_LOG_CACHE_PREFIX}{task_id}"
    task_log = cache.get(cache_key)

    if task_log is None:
        try:
            task_logs = TaskLog.objects.filter(task_id=task_id)
            if task_logs.exists():
                task_log = task_logs.first()
                # 只缓存必要的字段，避免缓存过大
                cache.set(
                    cache_key,
                    {
                        "id": task_log.id,
                        "task_id": task_log.task_id,
                        "task_name": task_log.task_name,
                        "status": task_log.status,
                        "start_time": (
                            task_log.start_time.isoformat()
                            if task_log.start_time
                            else None
                        ),
                    },
                    TASK_LOG_CACHE_TIMEOUT,
                )
        except Exception as e:
            logger.error(f"从数据库获取任务日志失败: {str(e)}")

    return task_log


def _invalidate_task_log_cache(task_id):
    """
    使任务日志缓存失效
    """
    cache_key = f"{TASK_LOG_CACHE_PREFIX}{task_id}"
    cache.delete(cache_key)


def _async_update_task_log(task_id, update_data):
    """
    异步更新任务日志
    """

    def _update_task():
        try:
            with transaction.atomic():
                task_log = (
                    TaskLog.objects.select_for_update().filter(task_id=task_id).first()
                )
                if task_log:
                    # 更新任务日志字段
                    for key, value in update_data.items():
                        setattr(task_log, key, value)
                    task_log.save()
                    # 使缓存失效
                    _invalidate_task_log_cache(task_id)
                    logger.debug(f"异步更新任务日志成功: {task_id}")
        except Exception as e:
            logger.error(f"异步更新任务日志失败: {task_id}, 错误: {str(e)}")
            # 可以在这里添加重试逻辑或死信队列处理

    # 提交到线程池执行
    ASYNC_EXECUTOR.submit(_update_task)


def _process_batched_updates():
    """
    处理批量更新任务日志
    """
    global _batched_updates, _last_batch_processed  # noqa: F824

    with _batch_lock:
        current_time = time.time()
        # 检查是否到达处理批次的时间
        if (
            current_time - _last_batch_processed < BATCH_UPDATE_INTERVAL
            or not _batched_updates
        ):
            return

        # 复制当前批次的更新并清空队列
        updates_to_process = _batched_updates.copy()
        _batched_updates.clear()
        _last_batch_processed = current_time

    try:
        with transaction.atomic():
            task_ids = list(updates_to_process.keys())
            # 批量获取任务日志
            task_logs = TaskLog.objects.filter(task_id__in=task_ids).select_for_update()

            # 构建任务ID到任务日志的映射
            task_log_map = {log.task_id: log for log in task_logs}

            # 更新任务日志
            for task_id, update_data in updates_to_process.items():
                if task_id in task_log_map:
                    task_log = task_log_map[task_id]
                    for key, value in update_data.items():
                        setattr(task_log, key, value)
                    task_log.save()
                    # 使缓存失效
                    _invalidate_task_log_cache(task_id)

        logger.debug(f"批量处理任务日志更新: {len(updates_to_process)} 条记录")
    except Exception as e:
        logger.error(f"批量处理任务日志更新失败: {str(e)}")


def _batch_update_task_log(task_id, update_data):
    """
    批量更新任务日志，减少数据库访问次数
    """
    with _batch_lock:
        if task_id not in _batched_updates:
            _batched_updates[task_id] = {}

        # 合并更新数据
        _batched_updates[task_id].update(update_data)

        # 检查是否需要立即处理（例如，如果有重要更新如任务完成）
        if "status" in update_data and update_data["status"] in [
            TaskLog.STATUS_FAILED,
            TaskLog.STATUS_SUCCESS,
            TaskLog.STATUS_REVOKED,
        ]:
            # 对于重要状态更新，立即处理
            _process_batched_updates()
            return

        # 否则，检查是否到达处理时间
        current_time = time.time()
        if current_time - _last_batch_processed >= BATCH_UPDATE_INTERVAL:
            # 异步处理批次更新
            ASYNC_EXECUTOR.submit(_process_batched_updates)


def setup_task_retry_handler():
    """
    设置任务重试处理器，更新任务日志状态
    优化点：
    1. 添加缓存机制减少数据库查询
    2. 异步处理更新操作，避免阻塞信号处理
    3. 批量处理相似更新，减少数据库访问次数
    4. 添加事务支持，确保数据一致性
    5. 添加错误处理和日志记录
    """
    from celery.signals import (task_failure, task_retry, task_revoked,
                                task_success, task_unknown)

    @task_retry.connect(sender=None)
    def handle_task_retry(sender=None, request=None, reason=None, **kwargs):
        """处理任务重试事件，更新任务日志状态"""
        try:
            task_id = request.id
            if task_id:
                # 使用异步批量更新
                _batch_update_task_log(
                    task_id,
                    {
                        "status": TaskLog.STATUS_RETRY,
                        "error_message": f"任务重试中: {str(reason)}",
                        "retry_count": (
                            TaskLog.objects.filter(task_id=task_id)
                            .values("retry_count")
                            .first()["retry_count"]
                            + 1
                            if TaskLog.objects.filter(task_id=task_id).exists()
                            else 1
                        ),
                    },
                )
                logger.debug(f"任务 {task_id} 进入重试状态，已加入批量更新队列")
        except Exception as e:
            logger.error(f"更新任务重试状态失败: {str(e)}")
            # 异常情况下使用异步单条更新作为备用
            _async_update_task_log(
                task_id,
                {
                    "status": TaskLog.STATUS_RETRY,
                    "error_message": f"任务重试中: {str(reason)}",
                    "retry_count": 1,
                },
            )

    @task_revoked.connect(sender=None)
    def handle_task_revoked(sender=None, request=None, terminated=None, **kwargs):
        """处理任务撤销事件，更新任务日志状态"""
        try:
            task_id = request.id
            if task_id:
                current_time = timezone.now()

                # 获取任务日志信息以计算持续时间
                task_log_info = _get_task_log_from_cache(task_id)
                duration = None
                if isinstance(task_log_info, dict) and task_log_info.get("start_time"):
                    # 从缓存计算持续时间
                    start_time = timezone.datetime.fromisoformat(
                        task_log_info["start_time"].replace("Z", "+00:00")
                    )
                    duration = (current_time - start_time).total_seconds()

                error_message = "任务已被撤销"
                if terminated:
                    error_message += " (强制终止)"

                # 任务撤销是重要状态变更，使用异步单条更新
                _async_update_task_log(
                    task_id,
                    {
                        "status": TaskLog.STATUS_REVOKED,
                        "error_message": error_message,
                        "end_time": current_time,
                        "duration": duration,
                    },
                )
                logger.info(f"任务 {task_id} 已被撤销，已提交异步更新")
        except Exception as e:
            logger.error(f"更新任务撤销状态失败: {str(e)}")

    @task_unknown.connect(sender=None)
    def handle_task_unknown(sender=None, request=None, **kwargs):
        """处理未知任务事件，创建任务日志"""
        try:
            task_id = request.id
            task_name = request.task

            # 检查是否已存在该任务的日志（使用缓存避免不必要的数据库查询）
            cache_key = f"{TASK_LOG_CACHE_PREFIX}{task_id}"
            task_log_exists = cache.get(f"{cache_key}_exists")

            if task_log_exists is None:
                # 缓存未命中，查询数据库
                task_log_exists = TaskLog.objects.filter(task_id=task_id).exists()
                cache.set(
                    f"{cache_key}_exists", task_log_exists, TASK_LOG_CACHE_TIMEOUT
                )

            if not task_log_exists:
                # 异步创建任务日志
                def _create_unknown_task_log():
                    try:
                        with transaction.atomic():
                            TaskLog.objects.create(
                                task_name=task_name,
                                task_id=task_id,
                                status=TaskLog.STATUS_FAILED,
                                args=safe_json_serialize(request.args),
                                kwargs=safe_json_serialize(request.kwargs),
                                error_message="未知任务",
                                start_time=timezone.now(),
                                end_time=timezone.now(),
                            )
                            # 更新缓存状态
                            cache.set(
                                f"{cache_key}_exists", True, TASK_LOG_CACHE_TIMEOUT
                            )
                            logger.warning(
                                f"创建未知任务日志: {task_name} (ID: {task_id})"
                            )
                    except Exception as e:
                        logger.error(f"创建未知任务日志失败: {str(e)}")

                ASYNC_EXECUTOR.submit(_create_unknown_task_log)
        except Exception as e:
            logger.error(f"处理未知任务事件失败: {str(e)}")

    @task_failure.connect(sender=None)
    def handle_task_failure(
        sender=None, task_id=None, exception=None, traceback=None, **kwargs
    ):
        """处理任务失败事件，更新任务日志状态（新增功能）"""
        try:
            if task_id:
                current_time = timezone.now()

                # 任务失败是重要状态变更，使用异步单条更新
                _async_update_task_log(
                    task_id,
                    {
                        "status": TaskLog.STATUS_FAILED,
                        "error_message": str(exception)[:1000],  # 限制错误信息长度
                        "end_time": current_time,
                    },
                )
                logger.debug(f"任务 {task_id} 执行失败，已提交异步更新")
        except Exception as e:
            logger.error(f"更新任务失败状态失败: {str(e)}")

    @task_success.connect(sender=None)
    def handle_task_success(sender=None, task_id=None, result=None, **kwargs):
        """处理任务成功事件，更新任务日志状态（新增功能）"""
        try:
            if task_id:
                current_time = timezone.now()

                # 任务成功是重要状态变更，使用异步单条更新
                _async_update_task_log(
                    task_id,
                    {
                        "status": TaskLog.STATUS_SUCCESS,
                        "result": str(result)[:2000],  # 限制结果长度
                        "end_time": current_time,
                    },
                )
                logger.debug(f"任务 {task_id} 执行成功，已提交异步更新")
        except Exception as e:
            logger.error(f"更新任务成功状态失败: {str(e)}")
