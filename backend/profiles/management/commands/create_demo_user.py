import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        username = os.getenv("DEMO_USERNAME", "reviewer")
        password = os.getenv("DEMO_PASSWORD", "ProfileSearch2026!")
        user, _ = get_user_model().objects.get_or_create(username=username)
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Demo user ready: {username}"))

