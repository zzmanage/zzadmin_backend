from rest_framework import serializers


class SystemOverviewSerializer(serializers.Serializer):
    """系统概览序列化器"""
    cpu_usage = serializers.FloatField(help_text="CPU使用率百分比")
    memory_usage = serializers.FloatField(help_text="内存使用率百分比")
    memory_total = serializers.IntegerField(help_text="总内存(字节)")
    memory_available = serializers.IntegerField(help_text="可用内存(字节)")
    disk_usage = serializers.FloatField(help_text="磁盘使用率百分比")
    disk_total = serializers.IntegerField(help_text="总磁盘空间(字节)")
    disk_free = serializers.IntegerField(help_text="可用磁盘空间(字节)")
    system_time = serializers.CharField(help_text="系统当前时间")
    running_processes = serializers.IntegerField(help_text="运行中的进程数")


class SystemMetricsSerializer(serializers.Serializer):
    """系统详细指标序列化器"""
    class CpuTimesSerializer(serializers.Serializer):
        user = serializers.FloatField(help_text="用户CPU时间")
        system = serializers.FloatField(help_text="系统CPU时间")
        idle = serializers.FloatField(help_text="空闲CPU时间")
    
    class CpuSerializer(serializers.Serializer):
        percent = serializers.FloatField(help_text="CPU使用率百分比")
        count = serializers.IntegerField(help_text="CPU核心数")
        times = CpuTimesSerializer(help_text="CPU时间分布")
    
    class MemorySerializer(serializers.Serializer):
        total = serializers.IntegerField(help_text="总内存(字节)")
        available = serializers.IntegerField(help_text="可用内存(字节)")
        used = serializers.IntegerField(help_text="已用内存(字节)")
        percent = serializers.FloatField(help_text="内存使用率百分比")
    
    class NetworkSerializer(serializers.Serializer):
        bytes_sent = serializers.IntegerField(help_text="发送字节数")
        bytes_recv = serializers.IntegerField(help_text="接收字节数")
        packets_sent = serializers.IntegerField(help_text="发送数据包数")
        packets_recv = serializers.IntegerField(help_text="接收数据包数")
    
    cpu = CpuSerializer(help_text="CPU信息")
    memory = MemorySerializer(help_text="内存信息")
    network = NetworkSerializer(help_text="网络信息")
    timestamp = serializers.IntegerField(help_text="时间戳")


class RedisStatusSerializer(serializers.Serializer):
    """Redis状态序列化器"""
    connected = serializers.BooleanField(help_text="连接状态")
    version = serializers.CharField(help_text="Redis版本", required=False, allow_blank=True)
    memory_usage = serializers.FloatField(help_text="内存使用量(MB)", required=False)
    memory_usage_percent = serializers.FloatField(help_text="内存使用率百分比", required=False)
    clients_connected = serializers.IntegerField(help_text="连接的客户端数", required=False)
    commands_processed = serializers.IntegerField(help_text="处理的命令数", required=False)
    uptime_in_seconds = serializers.IntegerField(help_text="运行时间(秒)", required=False)
    keyspace_hits = serializers.IntegerField(help_text="键空间命中数", required=False)
    keyspace_misses = serializers.IntegerField(help_text="键空间未命中数", required=False)
    error_message = serializers.CharField(help_text="错误信息", required=False, allow_blank=True)
    last_check_time = serializers.CharField(help_text="最后检查时间")


class RedisPerformanceSerializer(serializers.Serializer):
    """Redis性能指标序列化器"""
    latency = serializers.FloatField(help_text="延迟(毫秒)")
    throughput = serializers.IntegerField(help_text="吞吐量(每秒操作数)")
    hit_ratio = serializers.FloatField(help_text="命中率百分比")
    memory_fragmentation = serializers.FloatField(help_text="内存碎片率")
    db_keys = serializers.DictField(help_text="各数据库键数量", child=serializers.IntegerField())
    timestamp = serializers.IntegerField(help_text="时间戳")


class DatabaseStatusSerializer(serializers.Serializer):
    """数据库状态序列化器"""
    connected = serializers.BooleanField(help_text="连接状态")
    vendor = serializers.CharField(help_text="数据库厂商", required=False, allow_blank=True)
    version = serializers.CharField(help_text="数据库版本", required=False, allow_blank=True)
    active_connections = serializers.IntegerField(help_text="活动连接数", required=False)
    last_query_time = serializers.CharField(help_text="最后查询时间", required=False, allow_blank=True)
    error_message = serializers.CharField(help_text="错误信息", required=False, allow_blank=True)
    last_check_time = serializers.CharField(help_text="最后检查时间")


class DatabasePerformanceSerializer(serializers.Serializer):
    """数据库性能指标序列化器"""
    query_execution_time = serializers.FloatField(help_text="平均查询执行时间(秒)")
    transactions_per_second = serializers.IntegerField(help_text="每秒事务数")
    slow_queries = serializers.IntegerField(help_text="慢查询数")
    cache_hit_ratio = serializers.FloatField(help_text="缓存命中率百分比")
    deadlocks = serializers.IntegerField(help_text="死锁数")
    timestamp = serializers.IntegerField(help_text="时间戳")


class ServiceStatusSerializer(serializers.Serializer):
    """服务状态序列化器"""
    cpu_usage = serializers.FloatField(help_text="CPU使用率百分比")
    memory_usage = serializers.FloatField(help_text="内存使用率百分比")
    memory_used = serializers.IntegerField(help_text="已用内存(字节)")
    disk_usage = serializers.FloatField(help_text="磁盘使用率百分比")
    disk_used = serializers.IntegerField(help_text="已用磁盘空间(字节)")
    network_sent = serializers.IntegerField(help_text="发送字节数")
    network_recv = serializers.IntegerField(help_text="接收字节数")
    process_count = serializers.IntegerField(help_text="进程数")
    thread_count = serializers.IntegerField(help_text="线程数")
    timestamp = serializers.IntegerField(help_text="时间戳")
    last_check_time = serializers.CharField(help_text="最后检查时间")


class ProcessInfoSerializer(serializers.Serializer):
    """进程信息序列化器"""
    pid = serializers.IntegerField(help_text="进程ID")
    name = serializers.CharField(help_text="进程名称")
    cpu_percent = serializers.FloatField(help_text="CPU使用率百分比")
    memory_percent = serializers.FloatField(help_text="内存使用率百分比")
    create_time = serializers.CharField(help_text="创建时间")