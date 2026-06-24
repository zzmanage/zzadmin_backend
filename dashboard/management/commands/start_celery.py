import os
import platform
import subprocess
import sys
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "启动Celery工作进程和Beat服务，用于处理定时任务"

    def add_arguments(self, parser):
        # 添加命令行参数
        parser.add_argument(
            "--worker-only", action="store_true", help="仅启动Celery工作进程"
        )
        parser.add_argument(
            "--beat-only", action="store_true", help="仅启动Celery Beat服务"
        )
        parser.add_argument(
            "--loglevel",
            type=str,
            default="info",
            help="设置日志级别（debug, info, warning, error, critical）",
        )
        parser.add_argument(
            "--workers", type=int, default=1, help="设置Celery工作进程数量"
        )

    def handle(self, *args, **options):
        """处理命令执行逻辑"""
        self.stdout.write(self.style.SUCCESS("正在检查系统环境..."))

        # 检查Python环境
        python_version = platform.python_version()
        self.stdout.write(f"Python版本: {python_version}")

        # 检查Redis配置
        self._check_redis_config()

        # 获取命令行选项
        worker_only = options.get("worker_only")
        beat_only = options.get("beat_only")
        loglevel = options.get("loglevel")
        workers = options.get("workers")

        # 验证参数
        if worker_only and beat_only:
            raise CommandError("不能同时指定--worker-only和--beat-only参数")

        # 构建命令
        celery_commands = []

        # 获取Python可执行文件路径
        python_exe = sys.executable

        # 获取项目根目录
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

        # 设置工作目录
        os.chdir(project_root)

        if not beat_only:
            # 构建启动Celery工作进程的命令
            worker_cmd = [
                python_exe,
                "-m",
                "celery",
                "-A",
                "backend_management",
                "worker",
                f"--loglevel={loglevel}",
                f"--concurrency={workers}",
                "--pool=threads",
            ]
            celery_commands.append(("Celery工作进程", worker_cmd))

        if not worker_only:
            # 构建启动Celery Beat的命令
            beat_cmd = [
                python_exe,
                "-m",
                "celery",
                "-A",
                "backend_management",
                "beat",
                f"--loglevel={loglevel}",
                "--scheduler=django_celery_beat.schedulers:DatabaseScheduler",
            ]
            celery_commands.append(("Celery Beat服务", beat_cmd))

        # 启动进程
        processes = []
        try:
            self.stdout.write(self.style.SUCCESS("正在启动Celery服务..."))

            for service_name, cmd in celery_commands:
                self.stdout.write(f'启动{service_name}: {" ".join(cmd)}')

                # 在Windows上使用shell=True，确保正确处理命令
                shell = platform.system() == "Windows"

                # 启动进程
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=shell,
                    bufsize=1,
                )
                processes.append((service_name, proc))

                # 等待一小段时间确保进程启动
                time.sleep(1)

            self.stdout.write(self.style.SUCCESS("所有服务启动成功！"))
            self.stdout.write("-" * 60)
            self.stdout.write("注意：按Ctrl+C可以停止所有服务")
            self.stdout.write("-" * 60)

            # 轮询进程状态并输出日志
            self._monitor_processes(processes)

        except KeyboardInterrupt:
            self.stdout.write("\n接收到停止信号，正在关闭所有服务...")
        finally:
            # 清理进程
            self._cleanup_processes(processes)

    def _check_redis_config(self):
        """检查Redis配置是否正确设置"""
        # 检查是否已配置Redis连接
        if not hasattr(settings, "CHANNEL_LAYERS"):
            self.stdout.write(self.style.WARNING("警告: CHANNEL_LAYERS配置未找到"))
            return

        redis_config = settings.CHANNEL_LAYERS.get("default", {})
        if not redis_config:
            self.stdout.write(
                self.style.WARNING("警告: 默认的CHANNEL_LAYERS配置未找到")
            )
            return

        # 检查是否配置了Redis后端
        backend = redis_config.get("BACKEND")
        if not backend or "redis" not in backend.lower():
            self.stdout.write(self.style.WARNING("警告: 未配置Redis作为消息后端"))
            return

        # 检查连接配置
        config = redis_config.get("CONFIG", {})
        hosts = config.get("hosts", [])
        if not hosts:
            self.stdout.write(self.style.WARNING("警告: Redis主机配置未找到"))
            return

        self.stdout.write(f"Redis配置: {hosts[0]}")

    def _monitor_processes(self, processes):
        """监控进程状态并输出日志"""
        while processes:
            for i, (service_name, proc) in enumerate(processes.copy()):
                # 检查进程是否仍在运行
                if proc.poll() is not None:
                    # 进程已退出
                    exit_code = proc.poll()
                    self.stdout.write(
                        self.style.ERROR(f"{service_name}已退出，退出代码: {exit_code}")
                    )

                    # 读取错误输出
                    if proc.stderr:
                        error_output = proc.stderr.read().strip()
                        if error_output:
                            self.stdout.write(
                                self.style.ERROR(f"错误输出:\n{error_output}")
                            )

                    # 从列表中移除已退出的进程
                    processes.pop(i)
                else:
                    # 读取并输出标准输出（如果有）
                    if proc.stdout:
                        line = proc.stdout.readline()
                        if line:
                            self.stdout.write(f"[{service_name}] {line.strip()}")

            # 避免CPU占用过高
            time.sleep(0.1)

    def _cleanup_processes(self, processes):
        """清理所有进程"""
        for service_name, proc in processes:
            if proc.poll() is None:
                # 进程仍在运行，尝试终止
                self.stdout.write(f"正在停止{service_name}...")
                try:
                    proc.terminate()
                    # 等待进程终止，最多等待5秒
                    for _ in range(50):
                        if proc.poll() is not None:
                            break
                        time.sleep(0.1)
                    else:
                        # 超时后强制终止
                        proc.kill()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"停止{service_name}时出错: {str(e)}")
                    )

        self.stdout.write(self.style.SUCCESS("所有服务已停止"))
