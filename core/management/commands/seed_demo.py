"""
    python manage.py seed_demo                      # demo friends + fresh stories only
    python manage.py seed_demo --for ishan          # also connect them to your account
    python manage.py seed_demo --reset --for ishan  # wipe demo users first

Safe to re-run (never duplicates chats). Running it hourly from cron keeps the
Stories page populated, since stories expire after 24h.
"""

from django.core.management.base import BaseCommand, CommandError

from core import demo
from core.models import SnapUser


class Command(BaseCommand):
    help = "Create demo friends, chats, snaps, streaks, stories and map locations."

    def add_arguments(self, parser):
        parser.add_argument("--for", dest="targets", action="append", default=[],
                            help="Existing username to connect the demo friends to (repeatable).")
        parser.add_argument("--password", default=demo.DEMO_FRIEND_PASSWORD,
                            help="Password for newly created demo friend accounts.")
        parser.add_argument("--reset", action="store_true",
                            help="Delete all demo users (and their files) before seeding.")

    def handle(self, *args, targets, password, reset, **kwargs):
        target_users = []
        for name in targets:
            try:
                target_users.append(SnapUser.objects.get(username=name))
            except SnapUser.DoesNotExist:
                raise CommandError(f"User '{name}' not found. Register it on the site first.")

        if reset:
            self.stdout.write(f"Reset: deleted {demo.delete_demo_users()} demo objects.")

        friends = demo.ensure_demo_friends(password)
        for target in target_users:
            demo.seed_for(target, friends)
        demo.refresh_stories(friends)

        who = ", ".join(targets) if targets else "(no accounts — friends and stories only)"
        self.stdout.write(self.style.SUCCESS(f"Demo data ready for: {who}"))
