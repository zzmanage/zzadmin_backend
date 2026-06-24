# 代码质量检查指南

本指南介绍了项目中可用的代码质量检查工具和最佳实践，帮助开发人员确保代码符合项目规范。

## 1. 代码规范概述

项目遵循以下代码规范：

- 遵循PEP 8代码风格指南
- 最大行长度为100个字符
- 使用flake8进行代码质量检查

## 2. 可用的代码质量检查工具

### 2.1 长行检查工具

项目提供了两个版本的长行检查工具：

#### 原始版 (find_long_lines.py)

简单的脚本，仅检查指定文件中的长行。

```bash
python find_long_lines.py
```

**注意**：该脚本默认只检查`dashboard/utils/common_utils.py`文件，且找到第一个长行后就会停止。

#### 改进版 (find_long_lines_improved.py)

增强版的长行检查工具，具有以下特性：

- 递归检查目录下所有Python文件
- 可自定义最大行长度
- 支持排除特定目录或文件
- 格式化输出所有长行问题

**使用方法**：

```bash
# 检查当前目录下所有Python文件
python find_long_lines_improved.py

# 检查指定目录
python find_long_lines_improved.py dashboard/

# 自定义最大行长度
python find_long_lines_improved.py --max-length 120

# 排除特定目录
python find_long_lines_improved.py --exclude venv --exclude tests/
```

### 2.2 综合代码质量检查 (check_code_quality.py)

集成了长行检查和flake8代码规范检查的综合工具。

**使用方法**：

```bash
# 运行所有检查
python check_code_quality.py

# 只检查长行问题
python check_code_quality.py --only-lines

# 只检查flake8规范问题
python check_code_quality.py --only-flake8
```

### 2.3 直接使用flake8

```bash
# 检查整个项目
flake8 .

# 检查特定文件
flake8 dashboard/views_api.py
```

## 3. 代码格式化工具

项目提供了代码格式化脚本，可以自动格式化代码以符合规范：

### 3.1 format_code.py

基础版代码格式化工具。

```bash
python format_code.py
```

### 3.2 format_code_modified.py

增强版代码格式化工具，支持分批处理大量文件。

```bash
python format_code_modified.py
```

## 4. 项目更新脚本

`update_project.py`是一个综合脚本，可以执行多项操作，包括格式化代码和检查代码质量：

```bash
# 格式化代码
python update_project.py --format

# 检查代码质量
python update_project.py --quality

# 执行所有操作
python update_project.py --all
```

## 5. 常见问题及解决方案

### 5.1 E501 长行问题

**问题**：代码行超过了100个字符的限制。

**解决方案**：
1. 使用括号拆分长表达式
2. 将长字符串拆分为多个较短的字符串
3. 对于函数调用，可以将参数放在多行
4. 对于复杂的条件判断，可以将条件赋值给变量后再判断

**示例**：

```python
# 原始长行
logger.info(f"[{request_id}] 请求完成: {request.method} {request.path} 状态码: {response.status_code} 耗时: {process_time:.2f}ms")

# 修复后的代码
logger.info(
    f"[{request_id}] 请求完成: {request.method} {request.path} "
    f"状态码: {response.status_code} 耗时: {process_time:.2f}ms"
)
```

### 5.2 F401 未使用的导入

**问题**：导入了模块但没有在代码中使用。

**解决方案**：
1. 删除未使用的导入
2. 如果是有意导入（例如注册信号处理程序），可以使用`# noqa`注释标记

### 5.3 F841 未使用的变量

**问题**：变量被赋值但从未使用。

**解决方案**：
1. 删除未使用的变量
2. 如果是有意保留的变量，可以使用下划线前缀命名（如`_unused_var`）

### 5.4 F541 f-string缺少占位符

**问题**：使用了f-string语法但没有包含任何占位符。

**解决方案**：
1. 如果不需要插值，使用普通字符串（去掉f前缀）
2. 如果需要插值，添加适当的占位符

## 6. 集成到开发工作流程

为了确保代码质量，建议在以下时间点运行代码质量检查：

1. 提交代码前
2. 代码审查前
3. 合并分支前

可以将代码质量检查集成到IDE的保存操作中，或者配置git pre-commit钩子自动运行检查。

## 7. 最佳实践

1. **实时检查**：使用支持实时代码检查的IDE（如VSCode、PyCharm）
2. **频繁检查**：定期运行代码质量检查，不要等到问题积累过多
3. **持续改进**：根据团队反馈不断优化代码质量检查流程
4. **自动修复**：对于简单的格式问题，使用格式化工具自动修复
5. **代码审查**：在代码审查过程中关注代码质量问题