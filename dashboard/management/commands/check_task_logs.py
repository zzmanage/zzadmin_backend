# -*- coding: utf-8 -*-
"""
Django command to check task logs.
"""
from django.core.management.base import BaseCommand

from dashboard.models import TaskLog


class Command(BaseCommand):
    help = "检查任务日志记录"

    def add_arguments(self, parser):
        # 添加可选参数
        parser.add_argument(
            "--task-name",
            type=str,
            default="calculate_statistics",
            help="要检查的任务名称，默认为calculate_statistics",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="显示的日志数量上限，默认为20",
        )
        parser.add_argument(
            "--show-failed",
            action="store_true",
            help="仅显示失败的任务日志",
        )

    def handle(self, *args, **options):
        task_name = options["task_name"]
        limit = options["limit"]
        show_failed = options["show_failed"]

        if show_failed:
            # 仅查询失败的任务日志
            self.stdout.write(f"\n===== 失败的{task_name}任务日志 =====")
            task_logs = TaskLog.objects.filter(
                task_name=task_name, status=TaskLog.STATUS_FAILED
            ).order_by("-created_at")[:limit]
        else:
            # 查询所有任务日志（包括成功和失败的）
            self.stdout.write(f"\n===== 所有{task_name}任务日志 =====")
            task_logs = TaskLog.objects.filter(task_name=task_name).order_by(
                "-created_at"
            )[:limit]

        if task_logs:
            self.stdout.write(f"找到 {len(task_logs)} 条 {task_name} 任务日志记录：\n")
            for log in task_logs:
                self.stdout.write(f"任务ID: {log.task_id}")
                self.stdout.write(f"状态: {log.get_status_display()}")
                self.stdout.write(f"开始时间: {log.start_time}")
                self.stdout.write(f"结束时间: {log.end_time}")
                self.stdout.write(f"执行时长: {log.duration} 秒")
                self.stdout.write(f"参数: {log.args}")
                self.stdout.write(f"关键字参数: {log.kwargs}")
                self.stdout.write(f"结果: {log.result}")
                self.stdout.write(
                    f"错误信息: {log.error_message if log.error_message else '无'}"
                )
                self.stdout.write("=" * 50)
        else:
            self.stdout.write(f"没有找到 {task_name} 任务的日志记录")

        if not show_failed:
            # 单独查询失败的任务日志
            self.stdout.write(f"\n===== 失败的{task_name}任务日志 =====")
            failed_logs = TaskLog.objects.filter(
                task_name=task_name, status=TaskLog.STATUS_FAILED
            ).order_by("-created_at")

            if failed_logs:
                self.stdout.write(
                    f"找到 {len(failed_logs)} 条失败的 {task_name} 任务日志记录：\n"
                )
                for log in failed_logs[:limit]:  # 限制显示数量，避免输出过多
                    self.stdout.write(f"任务ID: {log.task_id}")
                    self.stdout.write(f"状态: {log.get_status_display()}")
                    self.stdout.write(f"开始时间: {log.start_time}")
                    self.stdout.write(f"结束时间: {log.end_time}")
                    self.stdout.write(f"执行时长: {log.duration} 秒")
                    self.stdout.write(f"参数: {log.args}")
                    self.stdout.write(f"关键字参数: {log.kwargs}")
                    self.stdout.write(f"结果: {log.result}")
                    self.stdout.write(
                        f"错误信息: {log.error_message if log.error_message else '无'}"
                    )
                    self.stdout.write("=" * 50)
            else:
                self.stdout.write(f"没有找到失败的 {task_name} 任务日志记录")
