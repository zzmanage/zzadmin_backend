"""
WebSocket消费者，用于处理消息通知
"""

import json
import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer


class NotificationConsumer(AsyncWebsocketConsumer):
    """处理WebSocket连接和消息通知"""

    async def connect(self):
        # 获取当前用户
        self.user = self.scope["user"]

        # 创建用户特定的频道组
        if self.user.is_authenticated:
            self.user_group_name = f"user_{self.user.id}"

            # 获取用户的角色和部门信息
            await self._add_user_to_groups()

            # 接受连接
            await self.accept()
        else:
            # 未认证用户拒绝连接
            await self.close()

    @database_sync_to_async
    def _get_user_groups(self):
        """同步获取用户的角色和部门信息"""
        # 延迟导入模型
        from django.contrib.auth.models import Group

        groups = []
        # 获取用户的角色组
        for group in self.user.groups.all():
            groups.append(f"role_{group.id}")

        # 获取用户的部门
        if (
            hasattr(self.user, "profile")
            and hasattr(self.user.profile, "department")
            and self.user.profile.department
        ):
            groups.append(f"department_{self.user.profile.department.id}")

        return groups

    async def _add_user_to_groups(self):
        """将用户添加到相应的频道组"""
        # 添加到用户特定组
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        # 添加到角色和部门组
        user_groups = await self._get_user_groups()
        for group_name in user_groups:
            await self.channel_layer.group_add(group_name, self.channel_name)

    async def disconnect(self, close_code):
        # 用户断开连接时，从所有组中移除
        if hasattr(self, "user_group_name") and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

            # 从角色和部门组中移除
            user_groups = await self._get_user_groups()
            for group_name in user_groups:
                await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """接收来自客户端的消息"""
        # 这里可以处理客户端发送的消息
        # 在这个简单实现中，我们不处理客户端消息
        pass

    async def send_notification(self, event):
        """向客户端发送通知"""
        # 获取消息数据
        message = event["message"]

        # 发送消息给WebSocket客户端
        await self.send(text_data=json.dumps({"type": "notification", "data": message}))

    @classmethod
    def _send_notification_to_group(cls, group_name, message):
        """向指定的频道组发送通知（内部辅助方法）"""
        channel_layer = get_channel_layer()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(
                channel_layer.group_send(
                    group_name, {"type": "send_notification", "message": message}
                )
            )
        finally:
            loop.close()

    @classmethod
    def send_notification_to_user(cls, user_id, message):
        """发送通知给指定用户"""
        cls._send_notification_to_group(f"user_{user_id}", message)

    @classmethod
    def send_notification_to_role(cls, role_id, message):
        """发送通知给指定角色的所有用户"""
        cls._send_notification_to_group(f"role_{role_id}", message)

    @classmethod
    def send_notification_to_department(cls, department_id, message):
        """发送通知给指定部门的所有用户"""
        cls._send_notification_to_group(f"department_{department_id}", message)


# 为了保持向后兼容性，保留原有的函数接口
def send_notification_to_user(user_id, message):
    """发送通知给指定用户（向后兼容接口）"""
    NotificationConsumer.send_notification_to_user(user_id, message)


def send_notification_to_role(role_id, message):
    """发送通知给指定角色的所有用户（向后兼容接口）"""
    NotificationConsumer.send_notification_to_role(role_id, message)


def send_notification_to_department(department_id, message):
    """发送通知给指定部门的所有用户（向后兼容接口）"""
    NotificationConsumer.send_notification_to_department(department_id, message)
