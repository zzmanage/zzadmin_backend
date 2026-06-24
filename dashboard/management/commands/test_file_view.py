"""Django management command to test the FileViewSet directly"""

from django.core.management.base import BaseCommand
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from dashboard.views.file_views import FileViewSet
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Tests the FileViewSet directly to diagnose the NameError issue"

    def handle(self, *args, **options):
        self.stdout.write("Testing FileViewSet directly...")

        try:
            # Create a mock request
            factory = RequestFactory()
            request = factory.get(
                "/api/files/?name=&category=&file_type=&uploader_id=&page=1&pageSize=10"
            )

            # Create a test user and attach to request
            try:
                user = User.objects.get(id=1)
            except User.DoesNotExist:
                self.stdout.write("Creating test user...")
                user = User.objects.create_user(
                    username="testuser", password="password"
                )

            request.user = user

            # Initialize the view
            view = FileViewSet.as_view({"get": "list"})

            # Execute the view
            self.stdout.write("Executing view...")
            response = view(request)

            # Check the response
            self.stdout.write(f"Response status code: {response.status_code}")
            self.stdout.write(f"Response data type: {type(response.data)}")

            # Try to access specific data if available
            if hasattr(response.data, "keys"):
                self.stdout.write(f"Response data keys: {list(response.data.keys())}")
                if "count" in response.data:
                    self.stdout.write(f"Total items: {response.data.get('count')}")
                if "results" in response.data:
                    self.stdout.write(
                        f"Items in current page: {len(response.data.get('results'))}"
                    )

            self.stdout.write("\nTest completed successfully!")

        except Exception as e:
            self.stdout.write(f"\nERROR: {str(e)}")
            import traceback

            self.stdout.write(f"\n{traceback.format_exc()}")
            self.stdout.write("\nTest failed.")
            return 1

        return 0
