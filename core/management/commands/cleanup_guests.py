"""
    python manage.py cleanup_guests            # delete demo guests older than 24h
    python manage.py cleanup_guests --hours 6
"""

from django.core.management.base import BaseCommand

from core import demo


class Command(BaseCommand):
    help = "Delete throwaway 'Try the demo' guest accounts (and their uploaded files)."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24)

    def handle(self, *args, hours, **kwargs):
        n = demo.cleanup_guests(older_than_hours=hours)
        self.stdout.write(self.style.SUCCESS(f"Deleted {n} objects from guests older than {hours}h."))
