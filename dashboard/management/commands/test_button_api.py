from django.core.management.base import BaseCommand
from rest_framework.test import APIClient
from django.urls import reverse
import json


class Command(BaseCommand):
    help = "测试按钮列表API功能"

    def handle(self, *args, **options):
        # 创建API客户端
        client = APIClient()

        # 获取按钮列表API的URL
        url = reverse("dashboard:button-list")

        self.stdout.write(f"测试按钮列表API: {url}")

        # 发送GET请求
        response = client.get(url)

        # 打印响应状态码和内容
        self.stdout.write(f"状态码: {response.status_code}")

        # 尝试解析JSON响应
        try:
            data = response.json()
            self.stdout.write(f"解析后的JSON数据:")
            self.stdout.write(json.dumps(data, ensure_ascii=False, indent=2))

            # 检查返回的数据结构是否符合预期
            if "results" in data:
                self.stdout.write(f'成功获取到{len(data["results"])}个按钮')

                # 打印按钮详情
                for button in data["results"]:
                    self.stdout.write(
                        f'按钮ID: {button.get("id")}, 名称: {button.get("name")}, 值: {button.get("value")}'
                    )
        except json.JSONDecodeError:
            self.stderr.write("无法解析响应为JSON")
            self.stderr.write(f"响应内容: {response.content.decode()}")
