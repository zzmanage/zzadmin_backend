import logging
import time
from datetime import datetime
import psutil
from enum import Enum, auto

logger = logging.getLogger(__name__)


def get_system_metrics():
    """获取系统核心指标"""
    try:
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 获取内存信息
        memory = psutil.virtual_memory()
        
        # 获取所有磁盘分区信息
        disk_partitions = psutil.disk_partitions(all=False)  # all=False表示只获取物理驱动器
        disks = []
        total_disk_stats = {"total": 0, "used": 0, "free": 0}
        
        for partition in disk_partitions:
            try:
                # 尝试获取每个分区的使用情况
                disk_usage = psutil.disk_usage(partition.mountpoint)
                
                # 累加总的磁盘统计信息
                total_disk_stats["total"] += disk_usage.total
                total_disk_stats["used"] += disk_usage.used
                total_disk_stats["free"] += disk_usage.free
                
                # 添加分区信息
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent
                })
            except (PermissionError, FileNotFoundError):
                # 忽略无法访问的分区
                continue
        
        # 计算总的磁盘使用率
        if total_disk_stats["total"] > 0:
            total_disk_stats["percent"] = (total_disk_stats["used"] / total_disk_stats["total"]) * 100
        else:
            total_disk_stats["percent"] = 0
        
        # 获取网络信息
        net_io = psutil.net_io_counters()
        
        # 构建系统指标数据
        metrics = {
            "cpu_usage": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            },
            "disk": total_disk_stats,  # 兼容原有结构，包含所有磁盘的总和
            "disks": disks,  # 新增字段，包含所有磁盘分区的详细信息
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "process_count": len(psutil.pids()),
            "timestamp": int(time.time())
        }
        
        return metrics
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        raise


def get_redis_status():
    """获取Redis连接状态和性能指标
    
    在实际应用中，这里应该连接Redis并获取真实状态
    当前实现返回模拟数据
    """
    try:
        # 模拟Redis状态数据
        redis_status = {
            "connected": True,
            "version": "6.2.5",
            "memory_usage": 128.5,  # MB
            "memory_usage_percent": 25.3,
            "clients_connected": 10,
            "commands_processed": 100000,
            "uptime_in_seconds": 86400,
            "keyspace_hits": 95000,
            "keyspace_misses": 5000,
            "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return redis_status
    except Exception as e:
        logger.error(f"获取Redis状态失败: {str(e)}")
        return {
            "connected": False,
            "error_message": str(e),
            "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def get_database_status():
    """获取数据库连接状态和性能指标"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # 执行简单查询检查连接
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # 获取数据库版本信息
            if connection.vendor == 'sqlite':
                cursor.execute("SELECT sqlite_version()")
            elif connection.vendor == 'postgresql':
                cursor.execute("SELECT version()")
            elif connection.vendor == 'mysql':
                cursor.execute("SELECT version()")
            elif connection.vendor == 'oracle':
                cursor.execute("SELECT * FROM v$version")
            
            version = cursor.fetchone()[0]
            
            # 构建数据库状态数据
            db_status = {
                "connected": True,
                "vendor": connection.vendor,
                "version": version,
                "active_connections": len(connection.queries),
                "last_query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return db_status
    except Exception as e:
        logger.error(f"获取数据库状态失败: {str(e)}")
        return {
            "connected": False,
            "error_message": str(e),
            "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def get_service_metrics():
    """获取服务运行指标"""
    try:
        # 获取系统指标
        system_metrics = get_system_metrics()
        
        # 获取线程数
        thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']))
        
        # 构建服务指标数据
        service_metrics = {
            "cpu_usage": system_metrics["cpu_usage"],
            "memory_usage": system_metrics["memory"]["percent"],
            "memory_used": system_metrics["memory"]["used"],
            "memory_total": system_metrics["memory"]["total"],
            "memory_available": system_metrics["memory"]["available"],
            "disk_usage": system_metrics["disk"]["percent"],
            "disk_used": system_metrics["disk"]["used"],
            "disk_total": system_metrics["disk"]["total"],
            "disk_free": system_metrics["disk"]["free"],
            "disks": system_metrics["disks"],  # 新增字段，包含所有磁盘分区的详细信息
            "network_sent": system_metrics["network"]["bytes_sent"],
            "network_recv": system_metrics["network"]["bytes_recv"],
            "process_count": system_metrics["process_count"],
            "thread_count": thread_count,
            "timestamp": system_metrics["timestamp"],
            "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return service_metrics
    except Exception as e:
        logger.error(f"获取服务指标失败: {str(e)}")
        raise


class ByteUnit(Enum):
    """字节单位枚举"""
    B = 'B'
    KB = 'KB'
    MB = 'MB'
    GB = 'GB'
    TB = 'TB'
    PB = 'PB'


def format_bytes(bytes_value):
    """格式化字节数，转换为人类可读的格式"""
    try:
        if bytes_value is None:
            return "0 B"
        
        # 将bytes_value转换为整数
        if isinstance(bytes_value, str):
            bytes_value = int(bytes_value)
        
        # 获取单位列表
        units = list(ByteUnit)
        
        # 确定使用的单位
        unit_index = 0
        while bytes_value >= 1024 and unit_index < len(units) - 1:
            bytes_value /= 1024
            unit_index += 1
        
        # 格式化输出
        unit = units[unit_index].value
        if unit_index == 0:
            return f"{bytes_value:.0f} {unit}"
        else:
            return f"{bytes_value:.2f} {unit}"
    except Exception as e:
        logger.error(f"格式化字节数失败: {str(e)}")
        return str(bytes_value)


def format_percent(percent_value, decimal_places=2):
    """格式化百分比"""
    try:
        if percent_value is None:
            return "0%"
        
        # 将percent_value转换为浮点数
        if isinstance(percent_value, str):
            percent_value = float(percent_value)
        
        # 格式化输出
        return f"{percent_value:.{decimal_places}f}%"
    except Exception as e:
        logger.error(f"格式化百分比失败: {str(e)}")
        return str(percent_value)


def format_time(timestamp):
    """格式化时间戳为人类可读的时间格式"""
    try:
        if timestamp is None:
            return "N/A"
        
        # 将timestamp转换为整数
        if isinstance(timestamp, str):
            timestamp = int(timestamp)
        
        # 格式化输出
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"格式化时间戳失败: {str(e)}")
        return str(timestamp)