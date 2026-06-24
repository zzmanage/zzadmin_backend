# -*- coding: utf-8 -*-
"""
Django command to format project code using black, isort and autopep8.
"""
import os
import subprocess
import sys
from typing import List

from django.core.management.base import BaseCommand

# 需要排除的目录和文件
EXCLUDE_DIRS = ["venv", "__pycache__", "migrations", ".git", "templates"]
EXCLUDE_FILES = ["manage.py"]


class Command(BaseCommand):
    help = "格式化项目中的所有Python代码"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check-only",
            action="store_true",
            help="仅检查代码格式，不进行实际格式化",
        )
        parser.add_argument(
            "--path",
            type=str,
            default=".",
            help="要格式化的目录路径，默认为当前目录",
        )

    def handle(self, *args, **options):
        check_only = options["check_only"]
        root_dir = options["path"]

        # 查找所有Python文件
        python_files = self.find_python_files(root_dir)
        self.stdout.write(f"找到 {len(python_files)} 个Python文件")

        if not python_files:
            return

        # 格式化代码
        try:
            self.format_with_isort(python_files, check_only)
            self.format_with_black(python_files, check_only)
            self.format_with_autopep8(python_files, check_only)

            # 使用flake8检查代码质量
            self.lint_with_flake8(python_files)

            self.stdout.write("\n代码格式化完成")
        except Exception as e:
            self.stderr.write(f"格式化过程中发生错误: {e}")
            sys.exit(1)

    def run_command(self, command: List[str], check: bool = True) -> None:
        """运行系统命令"""
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=check,
        )

    def find_python_files(self, root_dir: str) -> List[str]:
        """递归查找所有Python文件"""
        python_files = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 过滤掉排除的目录
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

            # 收集Python文件
            for filename in filenames:
                if (
                    filename.endswith(".py")
                    and filename not in EXCLUDE_FILES
                    and len(filename) > 3
                ):
                    full_path = os.path.join(dirpath, filename)
                    if os.path.isfile(full_path):
                        python_files.append(full_path)
        return python_files

    def format_with_isort(self, files: List[str], check_only: bool = False) -> None:
        """使用isort格式化Python文件的导入"""
        command = [sys.executable, "-m", "isort"]
        if check_only:
            command.append("--check")
        command.extend(files)
        self.run_command(command)

    def lint_with_flake8(self, files: List[str]) -> None:
        """使用flake8检查代码质量"""
        # 过滤掉无效的文件路径
        valid_files = []
        for file_path in files:
            if os.path.isfile(file_path) and file_path.endswith(".py"):
                valid_files.append(file_path)

        if not valid_files:
            return

        flake8_command = [
            sys.executable,
            "-m",
            "flake8",
            "--max-line-length=100",
            "--ignore=E203,W503",
        ] + valid_files

        # 即使flake8检查失败，也不要中断整个格式化过程
        self.run_command(flake8_command, check=False)

    def format_with_black(self, files: List[str], check_only: bool = False) -> None:
        """使用black格式化Python文件"""
        command = [sys.executable, "-m", "black"]
        if check_only:
            command.append("--check")
        command.extend(files)
        self.run_command(command)

    def format_with_autopep8(self, files: List[str], check_only: bool = False) -> None:
        """使用autopep8格式化Python文件"""
        command = [
            sys.executable,
            "-m",
            "autopep8",
            "--max-line-length=100",
            "--aggressive",
            "--aggressive",
        ]
        if not check_only:
            command.append("--in-place")
        command.extend(files)
        self.run_command(command)
