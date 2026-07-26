import random
from faker import Faker
from django.core.management.base import BaseCommand
from core.models import SnapUser, FriendRequest, Message

fake = Faker()


class Command(BaseCommand):
    help = "Seed messages for gupta"

    def handle(self, *args, **kwargs):

        gupta = SnapUser.objects.get(username="gupta")

        friends = FriendRequest.objects.filter(
            status="accepted"
        ).filter(
            from_user=gupta
        ) | FriendRequest.objects.filter(
            status="accepted",
            to_user=gupta
        )

        total = 0

        for fr in friends:

            friend = (
                fr.to_user
                if fr.from_user == gupta
                else fr.from_user
            )

            # Har friend ke saath 20-60 messages
            for _ in range(random.randint(20, 60)):

                sender = random.choice([gupta, friend])
                receiver = friend if sender == gupta else gupta

                Message.objects.create(
                    sender=sender,
                    receiver=receiver,
                    text_message=fake.sentence(
                        nb_words=random.randint(3, 10)
                    )
                )

                total += 1

        self.stdout.write(
            self.style.SUCCESS(f"{total} messages created.")
        )