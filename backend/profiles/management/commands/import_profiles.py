import json
from dataclasses import asdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from profiles.services.importer import ProfileImporter


class Command(BaseCommand):
    help = "Import LinkedIn profiles from CSV or JSON and emit a traceable quality report"
    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--report", default="reports/import-report.json")
    def handle(self, *args, **options):
        source = Path(options["path"])
        if not source.exists():
            raise CommandError(f"Dataset not found: {source}")
        report = ProfileImporter(source).run()
        output = Path(options["report"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Imported {report.imported_rows}/{report.raw_rows}; rejected {report.rejected_rows}; report: {output}"))
