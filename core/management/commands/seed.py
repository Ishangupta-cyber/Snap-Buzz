import random

from faker import Faker
from django.core.management.base import BaseCommand

from core.models import FriendRequest, Message

fake = Faker()


class Command(BaseCommand):

    help = "Generate messages between accepted friends"

    def handle(self, *args, **kwargs):

        accepted_requests = FriendRequest.objects.filter(status="accepted")

        total_messages = 0

        for request in accepted_requests:

            # Har friendship ke beech 15–40 messages
            for _ in range(random.randint(15, 40)):

                sender = random.choice(
                    [request.from_user, request.to_user]
                )

                receiver = (
                    request.to_user
                    if sender == request.from_user
                    else request.from_user
                )

                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    text_message=fake.sentence(
                        nb_words=random.randint(3, 10)
                    )
                )

                total_messages += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {total_messages} messages created."
            )
        )