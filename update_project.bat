@echo off
REM Windows批处理文件，用于运行项目自动化更新脚本

REM 设置中文显示
chcp 65001 >nul

REM 检查是否存在Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python并添加到系统PATH。
    pause
    exit /b 1
)

REM 检查是否存在update_project.py
if not exist update_project.py (
    echo 错误: 未找到update_project.py脚本。
    pause
    exit /b 1
)

REM 检查是否有虚拟环境
if exist venv\Scripts\activate (
    echo 激活虚拟环境...
    call venv\Scripts\activate
    if %errorlevel% neq 0 (
        echo 警告: 虚拟环境激活失败，尝试使用系统Python。
    )
)

REM 运行Python脚本，并传递所有命令行参数
python update_project.py %*

REM 暂停以便查看输出
pause