"""Django management command to test the file list view"""

from django.core.management.base import BaseCommand
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from dashboard.views.file_views import FileViewSet
from dashboard.models import File
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Tests the file list view directly to diagnose empty data issue"

    def handle(self, *args, **options):
        self.stdout.write("Testing FileViewSet list method directly...")

        try:
            # 首先检查数据库中的文件数量
            total_files = File.objects.count()
            self.stdout.write(f"Database file count: {total_files}")

            if total_files > 0:
                self.stdout.write("\nFirst 3 files in database:")
                for file in File.objects.all()[:3]:
                    self.stdout.write(
                        f"  - ID: {file.id}, Name: {file.name}, Size: {file.size} bytes"
                    )

            # Create a mock request
            factory = RequestFactory()
            request = factory.get(
                "/api/files/?name=&category=&file_type=&uploader_id=&page=1&pageSize=10"
            )

            # Get first superuser or create one
            user = User.objects.filter(is_superuser=True).first()

            if user:
                self.stdout.write(f"\nUsing superuser: {user.username}")
            else:
                self.stdout.write("\nCreating test superuser...")
                user = User.objects.create_superuser(
                    username="test_superuser",
                    email="test@example.com",
                    password="password",
                )
                self.stdout.write("Created superuser: test_superuser")

            # Set user on request
            request.user = user

            # Initialize the view
            view = FileViewSet.as_view({"get": "list"})

            # Execute the view
            self.stdout.write("\nExecuting view...")
            response = view(request)

            # Check the response
            self.stdout.write(f"Response status code: {response.status_code}")
            self.stdout.write(f"Response data type: {type(response.data)}")

            # Access specific data
            if hasattr(response.data, "keys"):
                self.stdout.write(f"Response data keys: {list(response.data.keys())}")
                if "count" in response.data:
                    self.stdout.write(
                        f"Total items in response: {response.data.get('count')}"
                    )
                if "results" in response.data:
                    results_count = len(response.data.get("results"))
                    self.stdout.write(f"Items in current page: {results_count}")

                    # Print first few items if available
                    if results_count > 0:
                        self.stdout.write("\nFirst 3 items in response:")
                        for item in response.data.get("results")[:3]:
                            self.stdout.write(
                                f"  - ID: {item.get('id')}, Name: {item.get('name')}"
                            )

            self.stdout.write("\n\nTest completed successfully!")

        except Exception as e:
            self.stdout.write(f"\n\nERROR: {str(e)}")
            import traceback

            self.stdout.write(f"\n{traceback.format_exc()}")
            self.stdout.write("\nTest failed.")

        # 不返回整数，避免AttributeError
        self.stdout.write("Command execution finished.")
