import django_filters
from django_filters import rest_framework as filters
from datetime import datetime, timedelta


class BaseMetricsFilter(filters.FilterSet):
    """监控指标基础过滤器"""
    # 时间范围过滤
    start_time = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte', help_text="开始时间")
    end_time = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte', help_text="结束时间")
    
    # 时间范围快捷过滤
    time_range = filters.ChoiceFilter(
        choices=[
            ('1h', '最近1小时'),
            ('6h', '最近6小时'),
            ('1d', '最近1天'),
            ('7d', '最近7天'),
            ('30d', '最近30天'),
        ],
        method='filter_time_range',
        help_text="时间范围快捷过滤"
    )
    
    def filter_time_range(self, queryset, name, value):
        """根据时间范围快捷选项过滤数据"""
        now = datetime.now()
        if value == '1h':
            start_time = now - timedelta(hours=1)
        elif value == '6h':
            start_time = now - timedelta(hours=6)
        elif value == '1d':
            start_time = now - timedelta(days=1)
        elif value == '7d':
            start_time = now - timedelta(days=7)
        elif value == '30d':
            start_time = now - timedelta(days=30)
        else:
            return queryset
        
        return queryset.filter(timestamp__gte=start_time)


class SystemMetricsFilter(BaseMetricsFilter):
    """系统指标过滤器"""
    # CPU使用率范围过滤
    cpu_usage_min = filters.NumberFilter(field_name='cpu__percent', lookup_expr='gte', help_text="CPU使用率最小值")
    cpu_usage_max = filters.NumberFilter(field_name='cpu__percent', lookup_expr='lte', help_text="CPU使用率最大值")
    
    # 内存使用率范围过滤
    memory_usage_min = filters.NumberFilter(field_name='memory__percent', lookup_expr='gte', help_text="内存使用率最小值")
    memory_usage_max = filters.NumberFilter(field_name='memory__percent', lookup_expr='lte', help_text="内存使用率最大值")


class RedisMetricsFilter(BaseMetricsFilter):
    """Redis指标过滤器"""
    # 连接状态过滤
    connected = filters.BooleanFilter(field_name='connected', help_text="连接状态")
    
    # 内存使用率范围过滤
    memory_usage_min = filters.NumberFilter(field_name='memory_usage_percent', lookup_expr='gte', help_text="内存使用率最小值")
    memory_usage_max = filters.NumberFilter(field_name='memory_usage_percent', lookup_expr='lte', help_text="内存使用率最大值")
    
    # 客户端连接数范围过滤
    clients_min = filters.NumberFilter(field_name='clients_connected', lookup_expr='gte', help_text="客户端连接数最小值")
    clients_max = filters.NumberFilter(field_name='clients_connected', lookup_expr='lte', help_text="客户端连接数最大值")


class DatabaseMetricsFilter(BaseMetricsFilter):
    """数据库指标过滤器"""
    # 连接状态过滤
    connected = filters.BooleanFilter(field_name='connected', help_text="连接状态")
    
    # 数据库类型过滤
    vendor = filters.CharFilter(field_name='vendor', lookup_expr='icontains', help_text="数据库厂商")
    
    # 活动连接数范围过滤
    connections_min = filters.NumberFilter(field_name='active_connections', lookup_expr='gte', help_text="活动连接数最小值")
    connections_max = filters.NumberFilter(field_name='active_connections', lookup_expr='lte', help_text="活动连接数最大值")


class ServiceMetricsFilter(BaseMetricsFilter):
    """服务指标过滤器"""
    # CPU使用率范围过滤
    cpu_usage_min = filters.NumberFilter(field_name='cpu_usage', lookup_expr='gte', help_text="CPU使用率最小值")
    cpu_usage_max = filters.NumberFilter(field_name='cpu_usage', lookup_expr='lte', help_text="CPU使用率最大值")
    
    # 内存使用率范围过滤
    memory_usage_min = filters.NumberFilter(field_name='memory_usage', lookup_expr='gte', help_text="内存使用率最小值")
    memory_usage_max = filters.NumberFilter(field_name='memory_usage', lookup_expr='lte', help_text="内存使用率最大值")
    
    # 磁盘使用率范围过滤
    disk_usage_min = filters.NumberFilter(field_name='disk_usage', lookup_expr='gte', help_text="磁盘使用率最小值")
    disk_usage_max = filters.NumberFilter(field_name='disk_usage', lookup_expr='lte', help_text="磁盘使用率最大值")