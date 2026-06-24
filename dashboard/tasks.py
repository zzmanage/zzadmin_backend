import logging
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import OperationLog, TaskLog, User
from .utils.task_utils import setup_task_retry_handler, task_with_logging

# 配置日志记录器
logger = logging.getLogger(__name__)

# 初始化重试处理器
setup_task_retry_handler()


@shared_task
@task_with_logging
def clean_old_logs(days=30):
    """
    清理指定天数前的操作日志

    Args:
        days: 保留最近多少天的日志，默认为30天
    """
    from datetime import timedelta

    # 导入update_task_progress函数
    from .utils.task_utils import update_task_progress

    # 计算截止日期
    cutoff_date = timezone.now() - timedelta(days=days)

    # 更新进度
    update_task_progress(0, "开始清理日志")

    # 清理操作日志
    operation_logs_count = OperationLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]

    # 更新进度
    update_task_progress(50, f"已清理 {operation_logs_count} 条操作日志")

    # 清理任务日志
    task_logs_count = TaskLog.objects.filter(created_at__lt=cutoff_date).delete()[0]

    # 更新进度
    update_task_progress(100, "日志清理完成")

    result_message = (
        f"成功清理 {operation_logs_count} 条操作日志, {task_logs_count} 条任务日志"
    )
    logger.info(result_message)

    return result_message


import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@shared_task(bind=True, max_retries=3, retry_backoff=5)
@task_with_logging
def send_reminder_email(self, user_id, message, subject='系统提醒', html_content=None):
    """
    发送提醒邮件给指定用户

    Args:
        self: 任务实例（用于重试操作）
        user_id: 用户ID
        message: 提醒消息内容
        subject: 邮件主题，默认为'系统提醒'
        html_content: 可选的HTML内容，如不提供则使用纯文本消息
    """
    try:
        # 获取用户信息
        user = User.objects.get(id=user_id)
        
        # 验证用户是否有有效的邮箱
        if not user.email:
            logger.warning(f"用户 {user.username} (ID: {user_id}) 没有有效的邮箱地址")
            return f"跳过发送邮件给用户 {user.username}：没有有效的邮箱地址"

        # 从配置中获取发件人信息
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'system@example.com')
        
        # 记录发送信息
        logger.info(f"准备发送邮件给用户 {user.username} ({user.email}): {subject}")
        
        if html_content:
            # 发送HTML邮件
            email = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html_content),  # 纯文本版本
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
        else:
            # 发送纯文本邮件
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )

        result_message = f"邮件已成功发送给用户 {user.username} ({user.email})"
        logger.info(result_message)
        
        return result_message
    
    except User.DoesNotExist:
        logger.error(f"用户ID {user_id} 不存在")
        return f"发送邮件失败：用户ID {user_id} 不存在"
    
    except Exception as e:
        logger.error(f"发送邮件给用户 {user_id} 失败: {str(e)}")
        
        # 重试任务（如果未达到最大重试次数）
        if not self.request.retries >= self.max_retries:
            logger.info(f"将在5秒后重试发送邮件...")
            raise self.retry(exc=e, countdown=5 * (2 ** self.request.retries))
        
        # 如果达到最大重试次数，返回失败信息
        return f"发送邮件失败（已重试最大次数）：{str(e)}"


@shared_task
@task_with_logging
def system_health_check():
    """
    系统健康检查任务
    定期检查系统状态并记录日志
    """
    # 获取当前系统时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 记录系统健康状态
    logger.info(f"系统健康检查 - 当前时间: {current_time}")

    # 在实际项目中，可以添加更多的检查项目，如数据库连接状态、磁盘空间等

    result_message = f"系统健康检查完成 - {current_time}"

    return result_message


@shared_task
@task_with_logging
def calculate_statistics(**kwargs):
    """
    计算系统统计数据
    定期计算用户活跃度、操作频率等统计信息
    """
    # 原有业务逻辑
    total_users = User.objects.count()
    today = timezone.now().date()
    today_logs = OperationLog.objects.filter(created_at__date=today).count()

    result_message = f"系统统计 - 用户总数: {total_users}, 今日操作日志数: {today_logs}"
    logger.info(result_message)

    return result_message
