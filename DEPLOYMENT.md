# 生产环境部署指南

本指南详细介绍如何在生产环境中部署和运行后端管理系统。

## 环境准备

### 操作系统要求
- Linux/Unix (推荐Ubuntu 22.04+ 或 CentOS 8+)
- Windows Server 2022+ (支持但不推荐)

### 必需软件
1. Python 3.10+<br>
2. Redis 6.0+ (用于Celery和WebSocket支持)<br>
3. 数据库 (推荐PostgreSQL 14+或MySQL 8.0+，默认SQLite)
4. Web服务器 (推荐Nginx 1.20+)

## 部署选项概览

系统支持三种部署方式：
1. **单一Daphne服务**：简单部署，同时处理HTTP和WebSocket请求
2. **分离式部署**：使用Gunicorn处理HTTP请求，Daphne处理WebSocket请求
3. **Docker容器化部署**：使用Docker和Docker Compose容器化部署，简化环境配置

## 安装步骤

### 1. 克隆代码库
```bash
# 克隆代码仓库
git clone https://github.com/your-username/backend_management_system.git
cd backend_management_system
```

### 2. 创建虚拟环境
```bash
# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. 安装依赖
```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

1. 复制示例环境文件
```bash
cp .env.example .env
```

2. 编辑.env文件，设置生产环境配置
```bash
# 生成安全的密钥
# 在Python shell中执行:
# python -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Redis配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 如果使用其他数据库，请配置相应参数
# DATABASE_ENGINE=django.db.backends.postgresql
# DATABASE_NAME=your-database-name
# DATABASE_USER=your-database-user
# DATABASE_PASSWORD=your-database-password
# DATABASE_HOST=your-database-host
# DATABASE_PORT=5432
```

### 5. 运行数据库迁移
```bash
# 应用数据库迁移
python manage.py migrate
```

### 6. 创建超级用户
```bash
# 创建管理员账号
python manage.py createsuperuser
```

### 7. 收集静态文件
```bash
# 收集静态文件到static_root目录
python manage.py collectstatic --noinput
```

## 配置生产环境服务

### 选项1：使用单一Daphne服务同时处理HTTP和WebSocket请求

Daphne作为ASGI服务器，本身就支持同时处理HTTP请求（充当WSGI服务器角色）和WebSocket请求。这种方式可以简化部署架构，减少需要管理的服务数量。

1. Daphne已在requirements.txt中包含，无需额外安装

2. 启动Daphne服务
```bash
daphne -b 127.0.0.1 -p 8000 backend_management.asgi:application
```

### 选项2：使用Gunicorn作为WSGI服务器 + Daphne作为ASGI服务器（分离式部署）

如果需要更精细的控制或特定性能优化，可以使用分离式部署方案。

#### 使用Gunicorn作为WSGI服务器

1. 安装Gunicorn
```bash
pip install gunicorn
```

2. 创建Gunicorn配置文件
```bash
# gunicorn_config.py
bind = '127.0.0.1:8000'
workers = 3  # 推荐值: 2 * CPU核心数 + 1
worker_class = 'sync'
max_requests = 1000
max_requests_jitter = 50
accesslog = '-'  # 输出到stdout
errorlog = '-'   # 输出到stderr
loglevel = 'info'
```

3. 启动Gunicorn服务
```bash
gunicorn --config gunicorn_config.py backend_management.wsgi
```

#### 配置Daphne作为ASGI服务器 (用于WebSocket)

1. Daphne已在requirements.txt中包含，无需额外安装

2. 启动Daphne服务
```bash
daphne -b 127.0.0.1 -p 8001 backend_management.asgi:application
```

### 配置Celery

1. 启动Celery worker
```bash
celery -A backend_management worker --loglevel=info
```

2. 启动Celery beat (用于定时任务)
```bash
celery -A backend_management beat --loglevel=info
```

## 配置Nginx反向代理

### 选项1：单一Daphne服务的Nginx配置

如果选择使用单一Daphne服务，请使用以下Nginx配置：

```nginx
# /etc/nginx/sites-available/backend_management
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    charset utf-8;

    # 静态文件服务
    location /static/ {
        alias /path/to/backend_management_system/static_root/;
        expires 30d;
    }

    # 媒体文件服务
    location /media/ {
        alias /path/to/backend_management_system/media/;
        expires 30d;
    }

    # WebSocket请求配置
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # 其他HTTP请求配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 选项2：分离式部署的Nginx配置

如果选择使用Gunicorn+Daphne的分离式部署方案，请使用以下Nginx配置：

```nginx
# /etc/nginx/sites-available/backend_management
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    charset utf-8;

    # 静态文件服务
    location /static/ {
        alias /path/to/backend_management_system/static_root/;
        expires 30d;
    }

    # 媒体文件服务
    location /media/ {
        alias /path/to/backend_management_system/media/;
        expires 30d;
    }

    # WebSocket请求配置
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # 其他HTTP请求配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 安装Nginx
```bash
# Ubuntu/Debian
apt update && apt install nginx

# CentOS/RHEL
yum install nginx
```

### 启用配置并重启Nginx
```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/backend_management /etc/nginx/sites-enabled/

# 测试配置是否正确
sudo nginx -t

# 重启Nginx服务
sudo systemctl restart nginx
```

## 使用Systemd管理服务

### 选项1：使用单一Daphne服务的Systemd配置

如果选择使用单一Daphne服务同时处理HTTP和WebSocket请求，可以使用以下配置：

```ini
# /etc/systemd/system/backend_management.service
[Unit]
Description=Backend Management System (Daphne ASGI Server)
after=network.target redis.target
Wants=redis.service

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/backend_management_system
environmentFile=/path/to/backend_management_system/.env
ExecStart=/path/to/backend_management_system/venv/bin/daphne -b 127.0.0.1 -p 8000 backend_management.asgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable backend_management celery celery-beat
sudo systemctl start backend_management celery celery-beat
```

### 选项2：分离式部署的Systemd配置

如果选择使用Gunicorn+Daphne的分离式部署方案，可以使用以下配置：

#### Gunicorn服务
```ini
# /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon for backend_management
after=network.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/backend_management_system
environmentFile=/path/to/backend_management_system/.env
ExecStart=/path/to/backend_management_system/venv/bin/gunicorn --config /path/to/backend_management_system/gunicorn_config.py backend_management.wsgi

[Install]
WantedBy=multi-user.target
```

#### Daphne服务
```ini
# /etc/systemd/system/daphne.service
[Unit]
Description=Daphne ASGI server for backend_management
after=network.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/backend_management_system
environmentFile=/path/to/backend_management_system/.env
ExecStart=/path/to/backend_management_system/venv/bin/daphne -b 127.0.0.1 -p 8001 backend_management.asgi:application

[Install]
WantedBy=multi-user.target
```

### Celery服务
```ini
# /etc/systemd/system/celery.service
[Unit]
Description=Celery worker for backend_management
after=network.target redis.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/backend_management_system
environmentFile=/path/to/backend_management_system/.env
ExecStart=/path/to/backend_management_system/venv/bin/celery -A backend_management worker --loglevel=info

[Install]
WantedBy=multi-user.target
```

### Celery Beat服务
```ini
# /etc/systemd/system/celery-beat.service
[Unit]
Description=Celery beat for backend_management
after=network.target redis.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/backend_management_system
environmentFile=/path/to/backend_management_system/.env
ExecStart=/path/to/backend_management_system/venv/bin/celery -A backend_management beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

### 启用并启动所有服务
```bash
sudo systemctl daemon-reload

sudo systemctl enable gunicorn daphne celery celery-beat
sudo systemctl start gunicorn daphne celery celery-beat
```

## 选项3：Docker容器化部署

使用Docker容器化部署可以简化环境配置，确保开发、测试和生产环境的一致性。

### 安装Docker和Docker Compose

```bash
# Ubuntu/Debian
apt update && apt install docker.io docker-compose

# CentOS/RHEL
yum install docker docker-compose

# 启动Docker服务
systemctl start docker
systemctl enable docker
```

### 创建Docker配置文件

在项目根目录创建以下文件：

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "backend_management.wsgi:application", "--bind", "0.0.0.0:8000"]
```

#### docker-compose.yml

```yaml
version: '3'

services:
  web:
    build: .
    command: gunicorn backend_management.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - SECRET_KEY=your-production-secret-key
      - ALLOWED_HOSTS=your-domain.com,www.your-domain.com
      - DATABASE_URL=postgres://postgres:postgres@db:5432/backend_management
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
  
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=backend_management
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
  
  redis:
    image: redis:6
    volumes:
      - redis_data:/data
  
  celery_worker:
    build: .
    command: celery -A backend_management worker --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - web
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
  
  celery_beat:
    build: .
    command: celery -A backend_management beat --loglevel=info
    volumes:
      - .:/app
    depends_on:
      - web
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./static_root:/app/static_root
      - ./media:/app/media
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

#### nginx.conf

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com www.your-domain.com;
    charset utf-8;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # 静态文件服务
    location /static/ {
        alias /app/static_root/;
        expires 30d;
    }

    # 媒体文件服务
    location /media/ {
        alias /app/media/;
        expires 30d;
    }

    # 其他HTTP请求配置
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker部署步骤

1. **准备环境配置**

   创建`.env`文件，配置生产环境变量：

   ```bash
   cp .env.example .env
   # 编辑.env文件，设置生产环境配置
   ```

2. **构建和启动容器**

   ```bash
   # 构建Docker镜像
   docker-compose build
   
   # 运行数据库迁移
   docker-compose run web python manage.py migrate
   
   # 创建超级用户
   docker-compose run web python manage.py createsuperuser
   
   # 启动所有服务
   docker-compose up -d
   ```

3. **申请SSL证书**

   ```bash
   # 停止Nginx容器
   docker-compose stop nginx
   
   # 申请SSL证书
   certbot certonly --standalone -d your-domain.com -d www.your-domain.com
   
   # 重新启动Nginx容器
   docker-compose start nginx
   ```

4. **查看容器状态**

   ```bash
   # 查看所有容器状态
   docker-compose ps
   
   # 查看日志
   docker-compose logs -f
   
   # 进入容器
   docker-compose exec web /bin/bash
   ```

### Docker部署注意事项

- 确保生产环境的`.env`文件配置安全的密钥和密码
- 定期备份数据库和重要数据
- 配置Docker日志驱动，便于日志管理和分析
- 考虑使用Docker Swarm或Kubernetes进行容器编排，提高可用性

## 配置HTTPS (推荐)

使用Let's Encrypt获取免费SSL证书：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 申请SSL证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 设置自动续期
sudo certbot renew --dry-run
```

## 定期维护

1. **数据库备份**
   定期备份数据库，推荐使用自动化备份脚本。

2. **日志监控**
   设置日志监控，推荐使用ELK Stack或其他日志分析工具。

3. **系统更新**
   定期更新操作系统和依赖包。

4. **性能监控**
   使用监控工具（如Prometheus+Grafana）监控系统性能。

## 安全建议

1. 始终保持DEBUG=False
2. 使用强密码和定期更换密码
3. 限制数据库用户权限
4. 定期更新依赖包
5. 配置防火墙限制访问
6. 启用CSRF保护和XSS防护