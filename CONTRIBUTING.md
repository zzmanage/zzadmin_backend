# 贡献指南

感谢您考虑为这个项目做出贡献！以下是一些指导原则，帮助您参与到这个项目中来。

## 开发环境设置

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/backend_management_system.git
   cd backend_management_system
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   # 在Windows上
   venv\Scripts\activate
   # 在macOS/Linux上
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行数据库迁移**
   ```bash
   python manage.py migrate
   ```

5. **创建超级用户**
   ```bash
   python manage.py createsuperuser
   ```

6. **启动开发服务器**
   ```bash
   python manage.py runserver
   ```

## 代码规范

- 遵循PEP 8代码风格指南
- 为所有函数和方法添加文档字符串
- 为新功能添加测试用例
- 确保代码通过现有的测试

## 提交流程

1. **创建一个新分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **进行更改并提交**
   ```bash
   git add .
   git commit -m "描述你的更改"
   ```

3. **推送到远程仓库**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **创建Pull Request**
   - 在GitHub上导航到你的fork
   - 点击"New Pull Request"
   - 选择你的特性分支
   - 填写描述并提交

## 报告问题

如果你发现了问题，请在GitHub上创建一个Issue，并包含以下信息：
- 问题的详细描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（Python版本，Django版本等）

## 代码审查

所有的Pull Request都会经过代码审查。请确保你的代码符合项目的质量标准。

## 行为准则

请尊重其他贡献者，保持友好和建设性的沟通。

## 许可证

通过贡献到这个项目，你同意你的代码将在MIT许可证下发布。