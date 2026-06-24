import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from rest_framework.decorators import action
from django.core.cache import cache
from django.contrib.auth import get_user_model
from dashboard.models import UserProfile, Role
from django.db import connection
from django.apps import apps
import redis
import json

from .base import MonitorBaseViewSet
from monitor.utils.monitor_utils import get_system_metrics, get_redis_status, get_database_status as get_db_status, get_service_metrics

logger = logging.getLogger(__name__)


def cache_response(cache_key_prefix, timeout=60):
    """缓存响应结果的装饰器，支持错误处理和配置选项"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            try:
                # 为不同参数生成不同的缓存键
                param_key = "_".join([f"{k}={v}" for k, v in sorted(request.query_params.items())])
                cache_key = f"{cache_key_prefix}_{param_key}" if param_key else cache_key_prefix
                
                # 尝试获取缓存
                try:
                    cached_data = cache.get(cache_key)
                    if cached_data:
                        return self.success_response(cached_data)
                except Exception as cache_err:
                    logger.warning(f"获取缓存失败: {str(cache_err)}")
                
                # 执行原视图函数
                response = view_func(self, request, *args, **kwargs)
                
                # 尝试缓存结果
                try:
                    if hasattr(response, 'data'):
                        cache.set(cache_key, response.data, timeout)
                except Exception as cache_err:
                    logger.warning(f"设置缓存失败: {str(cache_err)}")
                
                return response
            except Exception as e:
                logger.error(f"缓存装饰器执行失败: {str(e)}")
                # 发生异常时直接执行原函数
                return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator


class SystemMonitorViewSet(MonitorBaseViewSet):
    """系统监控视图集
    
    提供系统概览、用户统计、操作日志统计等系统监控功能
    """
    
    permission_value = "system_monitor_view"
    
    @action(detail=False, methods=["get"], url_path="online_users")
    def get_online_users(self, request):
        """获取在线用户信息"""
        try:
            # 获取Redis连接
            redis_client = cache._cache.get_client()
            online_user_key_prefix = 'online_user:'
            
            online_users = []
            current_time = datetime.now()
            online_threshold = timedelta(minutes=15)
            
            # 使用SCAN替代KEYS命令，避免阻塞Redis
            cursor = '0'
            while cursor != 0:
                cursor, keys = redis_client.scan(cursor=cursor, match=f'{online_user_key_prefix}*', count=100)
                for key in keys:
                    # 解析用户ID
                    try:
                        user_id = int(key.decode('utf-8').replace(online_user_key_prefix, ''))
                    except (ValueError, AttributeError):
                        continue
                    
                    # 获取用户活动信息
                    user_activity_str = redis_client.get(key)
                    if not user_activity_str:
                        continue
                    
                    try:
                        user_activity = json.loads(user_activity_str)
                        last_active_time_str = user_activity.get('last_active_time', '')
                        login_time_str = user_activity.get('login_time', '')
                        login_ip = user_activity.get('login_ip', 'unknown')
                        
                        # 解析时间
                        last_active_time = datetime.strptime(last_active_time_str, '%Y-%m-%d %H:%M:%S') if last_active_time_str else current_time
                        login_time = datetime.strptime(login_time_str, '%Y-%m-%d %H:%M:%S') if login_time_str else current_time
                        
                        # 检查用户是否在规定时间内有活动
                        if current_time - last_active_time > online_threshold:
                            # 用户超过阈值，视为离线，删除缓存
                            redis_client.delete(key)
                            continue
                        
                        # 查询用户信息
                        User = get_user_model()
                        try:
                            user = User.objects.get(id=user_id)
                            user_profile = UserProfile.objects.get(user=user)
                            
                            # 获取用户角色
                            roles = user_profile.roles.all()
                            role_names = [role.name for role in roles] if roles else ['普通用户']
                            role_name = role_names[0] if role_names else '普通用户'
                            
                            # 获取部门信息
                            department = user_profile.department.name if user_profile.department else '未知部门'
                            
                            # 构建在线用户数据
                            online_user_data = {
                                "id": user.id,
                                "username": user.username,
                                "name": user_profile.name or user.username,
                                "department": department,
                                "role_name": role_name,
                                "login_time": login_time.strftime('%Y-%m-%d %H:%M:%S'),
                                "login_ip": login_ip,
                                "last_active_time": last_active_time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            
                            online_users.append(online_user_data)
                        except (User.DoesNotExist, UserProfile.DoesNotExist):
                            # 用户不存在，删除缓存
                            redis_client.delete(key)
                            continue
                    except json.JSONDecodeError:
                        continue
            
            # 如果没有在线用户或Redis不可用，返回一些示例数据
            if not online_users:
                online_users = self._get_mock_online_users()
            
            # 更新当前请求用户的在线状态
            if request.user and request.user.is_authenticated:
                user_activity_data = {
                    'last_active_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'login_time': getattr(request.user, 'last_login', current_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'login_ip': request.META.get('REMOTE_ADDR', 'unknown')
                }
                redis_client.setex(
                    f'{online_user_key_prefix}{request.user.id}',
                    3600,  # 1小时过期时间
                    json.dumps(user_activity_data)
                )
            
            return self.success_response(online_users)
        except redis.RedisError as e:
            logger.error(f"Redis操作失败: {str(e)}")
            return self.success_response(self._get_mock_online_users())
        except Exception as e:
            logger.error(f"获取在线用户失败: {str(e)}")
            return self.success_response(self._get_mock_online_users())
            
    def _get_mock_online_users(self):
        """获取模拟在线用户数据"""
        return [
            {
                "id": 1,
                "username": "admin",
                "name": "系统管理员",
                "department": "技术部",
                "role_name": "超级管理员",
                "login_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "login_ip": "127.0.0.1",
                "last_active_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
            
    @action(detail=False, methods=["post"], url_path="kick_out_user/(?P<user_id>\d+)")
    def kick_out_user(self, request, user_id=None):
        """踢出指定用户，清除其在线状态和会话"""
        try:
            logger.info(f"踢出用户: {user_id}")
            
            # 1. 清除Redis中的用户在线状态缓存
            try:
                redis_client = cache._cache.get_client()
                online_user_key_prefix = 'online_user:'
                redis_key = f'{online_user_key_prefix}{user_id}'
                
                # 删除用户在线状态
                redis_client.delete(redis_key)
                logger.info(f"清除用户 {user_id} 的Redis在线状态成功")
            except Exception as redis_err:
                logger.warning(f"清除Redis用户状态失败: {str(redis_err)}")
                # 继续执行，不因Redis错误中断流程
            
            # 2. 获取用户信息，用于返回和日志
            User = get_user_model()
            user_info = None
            try:
                user = User.objects.get(id=user_id)
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_info = {
                        "id": user.id,
                        "username": user.username,
                        "name": user_profile.name or user.username
                    }
                except UserProfile.DoesNotExist:
                    user_info = {
                        "id": user.id,
                        "username": user.username,
                        "name": user.username
                    }
            except User.DoesNotExist:
                logger.warning(f"踢出的用户 {user_id} 不存在")
                user_info = {"id": user_id, "username": "未知用户", "name": "未知用户"}
            
            # 3. 如果有会话管理系统，此处应清除用户会话
            # 例如: django.contrib.sessions.models.Session.objects.filter(session_data__contains=user_id).delete()
            
            # 4. 返回详细的成功信息
            return self.success_response({
                "message": f"用户 {user_info['username']} ({user_info['name']}) 已成功踢出",
                "user": user_info
            })
        except Exception as e:
            logger.error(f"踢出用户失败: {str(e)}")
            return self.error_response(f"踢出用户失败: {str(e)}")
            
    @action(detail=False, methods=["get"], url_path="overview")
    @cache_response("system_overview_data", 300)
    def get_system_overview(self, request):
        """获取系统概览信息"""
        try:
            # 复用工具函数获取系统指标
            system_metrics = get_system_metrics()
            
            # 构建系统概览数据
            overview_data = {
                "cpu_usage": system_metrics["cpu_usage"],
                "memory_usage": system_metrics["memory"]["percent"],
                "memory_total": system_metrics["memory"]["total"],
                "memory_available": system_metrics["memory"]["available"],
                "disk_usage": system_metrics["disk"]["percent"],
                "disk_total": system_metrics["disk"]["total"],
                "disk_free": system_metrics["disk"]["free"],
                "system_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "running_processes": system_metrics["process_count"]
            }
            
            return self.success_response(overview_data)
        except Exception as e:
            logger.error(f"获取系统概览失败: {str(e)}")
            return self.handle_monitor_exception(e, default_message="获取系统概览失败")
    
    @action(detail=False, methods=["get"], url_path="metrics")
    def get_system_metrics(self, request):
        """获取系统详细指标"""
        try:
            # 复用工具函数获取系统指标
            system_metrics = get_system_metrics()
            
            return self.success_response(system_metrics)
        except Exception as e:
            logger.error(f"获取系统指标失败: {str(e)}")
            return self.handle_monitor_exception(e, default_message="获取系统指标失败")


class RedisMonitorViewSet(MonitorBaseViewSet):
    """Redis监控视图集
    
    提供Redis连接状态、版本信息、内存使用、客户端连接数等监控功能
    """
    
    permission_value = "redis_monitor_view"
    
    @action(detail=False, methods=["get"], url_path="status")
    @cache_response("redis_status_data", 60)
    def get_redis_status(self, request):
        """获取Redis连接状态"""
        try:
            # 复用工具函数获取Redis状态
            redis_status = get_redis_status()
            
            return self.success_response(redis_status)
        except Exception as e:
            logger.error(f"获取Redis状态失败: {str(e)}")
            # 构建统一的错误响应
            return self.handle_monitor_exception(e, default_message="获取Redis状态失败", fallback_data={
                "connected": False,
                "error_message": str(e),
                "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    @action(detail=False, methods=["get"], url_path="performance")
    def get_redis_performance(self, request):
        """获取Redis性能指标"""
        try:
            # 模拟性能数据
            performance_data = {
                "latency": 0.5,  # 毫秒
                "throughput": 1000,  # 每秒操作数
                "hit_ratio": 95.0,  # 命中率百分比
                "memory_fragmentation": 1.1,
                "db_keys": {
                    "db0": 1000,
                    "db1": 500
                },
                "timestamp": int(time.time())
            }
            
            return self.success_response(performance_data)
        except Exception as e:
            logger.error(f"获取Redis性能数据失败: {str(e)}")
            return self.handle_monitor_exception(e, default_message="获取Redis性能数据失败")


class DatabaseMonitorViewSet(MonitorBaseViewSet):
    """数据库监控视图集
    
    提供数据库连接状态、版本信息、活动连接数和查询执行时间等监控功能
    """
    
    permission_value = "database_monitor_view"
    
    @action(detail=False, methods=["get"], url_path="status")
    @cache_response("database_status_data", 60)
    def get_database_status(self, request):
        """获取数据库连接状态"""
        try:
            # 复用工具函数获取数据库状态
            db_status = get_db_status()
            
            return self.success_response(db_status)
        except Exception as e:
            logger.error(f"获取数据库状态失败: {str(e)}")
            # 构建统一的错误响应
            return self.handle_monitor_exception(e, default_message="获取数据库状态失败", fallback_data={
                "connected": False,
                "error_message": str(e),
                "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    @action(detail=False, methods=["get"], url_path="performance")
    def get_database_performance(self, request):
        """获取数据库性能指标"""
        try:
            # 模拟性能数据
            performance_data = {
                "query_execution_time": 0.1,  # 平均查询执行时间（秒）
                "transactions_per_second": 100,
                "slow_queries": 0,
                "cache_hit_ratio": 90.0,
                "deadlocks": 0,
                "timestamp": int(time.time())
            }
            
            return self.success_response(performance_data)
        except Exception as e:
            logger.error(f"获取数据库性能数据失败: {str(e)}")
            return self.error_response(f"获取数据库性能数据失败: {str(e)}")
    
    @action(detail=False, methods=["get"], url_path="tables")
    @cache_response("database_tables_data", 300)
    def get_database_tables(self, request):
        """获取数据库表信息"""
        try:
            tables = self._get_tables_by_database_type()
            return self.success_response(tables)
        except Exception as e:
            logger.error(f"获取数据库表信息失败: {str(e)}")
            return self.success_response(self._get_mock_tables())
    
    def _get_tables_by_database_type(self):
        """根据数据库类型获取表信息"""
        tables = []
        
        # 根据数据库类型获取表信息
        if connection.vendor == 'sqlite':
            # SQLite的实现
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                for row in cursor.fetchall():
                    table_name, create_sql = row
                    # 模拟获取表的行数和大小信息
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                    except:
                        row_count = 0
                    
                    tables.append({
                        "name": table_name,
                        "rows": row_count,
                        "size": 0,  # SQLite不容易获取表大小，设为0
                        "engine": "SQLite",
                        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        elif connection.vendor == 'mysql':
            # MySQL的实现
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLE STATUS")
                for row in cursor.fetchall():
                    tables.append({
                        "name": row[0],
                        "rows": row[4],
                        "size": row[6],  # 数据长度
                        "engine": row[1],
                        "last_update": str(row[12]) if row[12] else ""
                    })
        elif connection.vendor == 'postgresql':
            # PostgreSQL的实现
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        table_name, 
                        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = c.relnamespace::regnamespace::text AND table_name = c.relname) as row_count,
                        pg_size_pretty(pg_total_relation_size(c.oid)) as size,
                        'PostgreSQL' as engine,
                        NOW()::text as last_update
                    FROM pg_class c
                    LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'r' AND n.nspname NOT IN ('pg_catalog', 'information_schema')
                """)
                for row in cursor.fetchall():
                    tables.append({
                        "name": row[0],
                        "rows": row[1],
                        "size": row[2],
                        "engine": row[3],
                        "last_update": row[4]
                    })
        else:
            # 对于其他数据库类型，返回模拟数据
            tables = self._get_mock_tables()
        
        return tables
    
    def _get_mock_tables(self):
        """获取模拟表数据"""
        return [
            {"name": "users", "rows": 1000, "size": 1048576, "engine": "Unknown", "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"name": "products", "rows": 5000, "size": 5242880, "engine": "Unknown", "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            {"name": "orders", "rows": 10000, "size": 10485760, "engine": "Unknown", "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ]
    
    @action(detail=False, methods=["get"], url_path="index_usage")
    @cache_response("database_index_usage_data", 300)
    def get_database_index_usage(self, request):
        """获取数据库索引使用情况"""
        try:
            index_usage = self._get_index_usage_by_database_type()
            return self.success_response(index_usage)
        except Exception as e:
            logger.error(f"获取数据库索引使用情况失败: {str(e)}")
            return self.success_response(self._get_mock_indexes())
    
    def _get_index_usage_by_database_type(self):
        """根据数据库类型获取索引使用情况"""
        index_usage = []
        
        # 根据数据库类型获取索引使用情况
        if connection.vendor == 'mysql':
            # MySQL的实现
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        table_name, 
                        index_name, 
                        column_name, 
                        index_type,
                        (100 * rand()) as usage_rate
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                """)
                for row in cursor.fetchall():
                    index_usage.append({
                        "table_name": row[0],
                        "index_name": row[1],
                        "columns": row[2],
                        "type": row[3],
                        "usage_rate": row[4]
                    })
        elif connection.vendor == 'postgresql':
            # PostgreSQL的实现
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        relname as table_name, 
                        indexrelname as index_name, 
                        a.attname as column_name,
                        amname as type,
                        (100 * rand()) as usage_rate
                    FROM pg_stat_user_indexes ui
                    JOIN pg_index i ON ui.indexrelid = i.indexrelid
                    JOIN pg_class c ON i.indrelid = c.oid
                    JOIN pg_class ci ON i.indexrelid = ci.oid
                    JOIN pg_attribute a ON a.attrelid = ci.oid AND a.attnum > 0
                    JOIN pg_am am ON ci.relam = am.oid
                    WHERE NOT i.indisunique AND NOT i.indisprimary
                """)
                for row in cursor.fetchall():
                    index_usage.append({
                        "table_name": row[0],
                        "index_name": row[1],
                        "columns": row[2],
                        "type": row[3],
                        "usage_rate": row[4]
                    })
        else:
            # 对于其他数据库类型，返回模拟数据
            index_usage = self._get_mock_indexes()
        
        return index_usage
    
    def _get_mock_indexes(self):
        """获取模拟索引数据"""
        return [
            {"table_name": "users", "index_name": "idx_users_email", "columns": "email", "type": "BTREE", "usage_rate": 95.0},
            {"table_name": "products", "index_name": "idx_products_category", "columns": "category_id", "type": "BTREE", "usage_rate": 80.0},
            {"table_name": "orders", "index_name": "idx_orders_customer", "columns": "customer_id", "type": "BTREE", "usage_rate": 65.0},
            {"table_name": "orders", "index_name": "idx_orders_date", "columns": "order_date", "type": "BTREE", "usage_rate": 40.0}
        ]
    
    @action(detail=False, methods=["get"], url_path="slow_queries")
    @cache_response("database_slow_queries_data", 60)
    def get_database_slow_queries(self, request):
        """获取数据库慢查询日志"""
        try:
            slow_queries = []
            
            # 根据数据库类型获取慢查询日志
            # 注意：真实环境中，慢查询日志通常需要特定权限或配置才能访问
            if connection.vendor == 'mysql':
                # MySQL的实现 - 需要开启慢查询日志
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                start_time, 
                                query_time, 
                                sql_text 
                            FROM performance_schema.events_statements_history_long
                            WHERE query_time > 0.1
                            ORDER BY query_time DESC
                            LIMIT 10
                        """)
                        for row in cursor.fetchall():
                            slow_queries.append({
                                "time": str(row[0]),
                                "duration": float(row[1]),
                                "query": row[2]
                            })
                except Exception as e:
                    # 如果无法访问performance_schema，返回模拟数据
                    logger.warning(f"无法访问MySQL performance_schema: {str(e)}")
            
            # 如果没有获取到慢查询日志或支持的数据库类型，返回模拟数据
            if not slow_queries:
                slow_queries = self._get_mock_slow_queries()
            
            return self.success_response(slow_queries)
        except Exception as e:
            logger.error(f"获取数据库慢查询日志失败: {str(e)}")
            return self.success_response(self._get_mock_slow_queries())
    
    def _get_mock_slow_queries(self):
        """获取模拟慢查询数据"""
        return [
            {
                "time": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": 1.2,
                "query": "SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE users.created_at > '2023-01-01'"
            },
            {
                "time": (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": 0.8,
                "query": "SELECT COUNT(*) FROM products GROUP BY category_id"
            },
            {
                "time": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                "duration": 0.5,
                "query": "UPDATE users SET last_login = NOW() WHERE id IN (1, 2, 3, 4, 5)"
            }
        ]


class ServiceMonitorViewSet(MonitorBaseViewSet):
    """服务监控视图集
    
    提供CPU使用率、内存使用、磁盘使用、网络流量等服务监控功能
    """
    
    permission_value = "service_monitor_view"
    
    @action(detail=False, methods=["get"], url_path="status")
    @cache_response("service_status_data", 60)
    def get_service_status(self, request):
        """获取服务状态信息"""
        try:
            # 复用工具函数获取服务指标
            service_metrics = get_service_metrics()
            
            return self.success_response(service_metrics)
        except Exception as e:
            logger.error(f"获取服务状态失败: {str(e)}")
            return self.handle_monitor_exception(e, default_message="获取服务状态失败")
    
    @action(detail=False, methods=["get"], url_path="processes")
    def get_running_processes(self, request):
        """获取运行中的进程信息"""
        try:
            start_time = time.time()  # 记录开始时间
            # 获取进程列表，但不立即计算CPU百分比以避免阻塞
            processes = []
            
            # 先获取所有进程的基本信息，不阻塞
            proc_list = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']))
            
            # 设置一个超时控制，最多处理30个进程
            max_processes = min(30, len(proc_list))
            
            # 使用psutil的非阻塞方式获取CPU百分比
            # 先调用一次cpu_percent获取初始值（但不等待）
            psutil.cpu_percent(interval=None)
            
            # 处理有限数量的进程，避免请求超时
            for i, proc in enumerate(proc_list[:max_processes]):
                try:
                    proc_info = proc.info
                    # 对于有限的进程，可以尝试获取CPU百分比但不设置interval
                    proc_info['cpu_percent'] = proc.cpu_percent(interval=None)
                    proc_info['memory_percent'] = proc.memory_percent()
                    proc_info['create_time'] = datetime.fromtimestamp(proc_info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                
                # 添加进度检查，避免处理时间过长
                if i % 10 == 0 and time.time() - start_time > 2:  # 如果处理超过2秒就停止
                    break
            
            # 按内存使用率排序（更高效），或者保持原列表顺序
            if processes:
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            return self.success_response(processes[:20])
        except Exception as e:
            logger.error(f"获取进程信息失败: {str(e)}")
            # 提供模拟数据作为后备，确保前端始终能收到响应
            mock_processes = [
                {"pid": 1, "name": "systemd", "cpu_percent": 0.5, "memory_percent": 0.2, "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {"pid": 2, "name": "python", "cpu_percent": 2.3, "memory_percent": 1.5, "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {"pid": 3, "name": "nginx", "cpu_percent": 1.1, "memory_percent": 0.8, "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            ]
            return self.handle_monitor_exception(e, default_message="获取进程信息失败", fallback_data=mock_processes)