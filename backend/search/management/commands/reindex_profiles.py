from django.core.management.base import BaseCommand

from search.indexer import rebuild_index


class Command(BaseCommand):
    help = "Rebuild the Elasticsearch profile index from PostgreSQL"
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Indexed {rebuild_index()} profiles"))
