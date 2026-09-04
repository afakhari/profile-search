import json
import os
from dataclasses import asdict
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from profiles.models import Profile
from profiles.services.importer import ProfileImporter
from search.indexer import rebuild_index


class Command(BaseCommand):
    help = "Idempotently create the demo user, seed an empty database, and rebuild search"

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="/data/raw/linkedin_profiles.csv")
        parser.add_argument("--report", default="/reports/import-report.json")

    def handle(self, *args, **options):
        username = os.getenv("DEMO_USERNAME", "reviewer")
        password = os.getenv("DEMO_PASSWORD", "ProfileSearch2026!")
        user, _ = get_user_model().objects.get_or_create(username=username)
        user.set_password(password)
        user.save()

        dataset = Path(options["dataset"])
        if not Profile.objects.exists() and dataset.exists():
            report = ProfileImporter(dataset).run()
            output = Path(options["report"])
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(f"Seeded {report.imported_rows} profiles")

        count = rebuild_index()
        self.stdout.write(self.style.SUCCESS(f"Bootstrap ready: {count} indexed profiles; user {username}"))
