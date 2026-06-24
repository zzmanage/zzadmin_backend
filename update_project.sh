#!/bin/bash

# Linux/macOS shell脚本，用于运行项目自动化更新脚本

# 设置字体颜色
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[0;33m'
blue='\033[0;34m'
reset='\033[0m'

# 检查是否存在Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${red}错误: 未找到Python。请先安装Python。${reset}"
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

# 检查是否存在update_project.py
if [ ! -f "update_project.py" ]; then
    echo -e "${red}错误: 未找到update_project.py脚本。${reset}"
    exit 1
fi

# 检查是否有虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo -e "${yellow}激活虚拟环境...${reset}"
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo -e "${yellow}警告: 虚拟环境激活失败，尝试使用系统Python。${reset}"
    fi
fi

# 运行Python脚本，并传递所有命令行参数
$PYTHON update_project.py "$@"

# 返回Python脚本的退出码
exit $?