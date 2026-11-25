"""
Demo data for Snap Buzz — makes the app look alive for visitors / recruiters.

    python manage.py seed_demo --for ishan              # connect demo friends to your account
    python manage.py seed_demo --for ishan --for demo   # several accounts
    python manage.py seed_demo --reset --for ishan      # wipe demo users first, then re-create

Creates 6 demo friends (with avatars, map locations, chats, snaps, streaks, stories)
and 2 pending friend requests. Safe to re-run: it never duplicates chats, and it
refreshes stories that expired (stories only live 24h) — so a daily cron keeps
the Stories page populated.
"""

import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from PIL import Image, ImageColor, ImageDraw, ImageFont

from core.models import Conversation, FriendRequest, Message, SnapUser, Story

# username, colour, city, lat, lng, streak
DEMO_FRIENDS = [
    ("aarav", "#8b5cf6", "Delhi", 28.6139, 77.2090, 12),
    ("priya", "#ec4899", "Mumbai", 19.0760, 72.8777, 27),
    ("rohan", "#06b6d4", "Bengaluru", 12.9716, 77.5946, 5),
    ("ananya", "#f59e0b", "Jaipur", 26.9124, 75.7873, 0),
    ("kabir", "#10b981", "Pune", 18.5204, 73.8567, 3),
    ("isha", "#ef4444", "Kolkata", 22.5726, 88.3639, 0),
]

# These users send YOU a friend request (shows on the Friend Requests page)
DEMO_PENDING = [
    ("meera", "#6366f1"),
    ("vihaan", "#14b8a6"),
]

DEMO_USERNAMES = [u[0] for u in DEMO_FRIENDS] + [u[0] for u in DEMO_PENDING]

# (from_friend, text) — None text + from_friend => a snap from the friend
CHATS = {
    "aarav": [
        (True, "Bhai kal ka match dekha?? 🔥"),
        (False, "Haan yaar last over was insane"),
        (True, "Weekend pe cricket khelne chalein?"),
        (False, "Pakka! Sunday morning 7 baje?"),
        (True, None),
    ],
    "priya": [
        (False, "Did you finish the DBMS assignment?"),
        (True, "Almost! Normalization wala part tricky hai 😅"),
        (False, "Send me your ER diagram once done"),
        (True, None),
        (True, "Check the snap 👆 that's the cafe I told you about"),
    ],
    "rohan": [
        (True, "Hackathon registration closes tonight!"),
        (False, "Already registered our team 🚀"),
        (True, "Legend. Idea finalize karte hain kal"),
    ],
    "ananya": [
        (False, "Happy birthday!! 🎂🎉"),
        (True, "Thank youuu 🥹"),
        (False, "Party kab hai?"),
    ],
    "kabir": [
        (True, "Pune ka weather mast hai aaj ☔"),
        (False, "Lucky! Yahan bahut garmi hai"),
        (True, None),
    ],
    "isha": [
        (True, "New Snap Buzz feature dekha? Streaks 🔥"),
        (False, "Yes! Mera 27 day streak chal raha hai priya ke saath"),
    ],
}

STORY_CAPTIONS = {
    "aarav": ["Morning run", "Chai time"],
    "priya": ["Marine Drive sunset", "Coffee date"],
    "rohan": ["Hackathon mode: ON"],
    "kabir": ["Monsoon vibes", "Weekend trek"],
    "isha": ["Durga Puja nights"],
}

SNAP_CAPTIONS = ["Look at this view!", "Guess where I am?", "Sunday mood", "Best momos in town"]


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def _gradient_image(color, size, text, font_size):
    """Vertical gradient with centred white text -> JPEG bytes."""
    w, h = size
    r, g, b = ImageColor.getrgb(color)
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        draw.line([(0, y), (w, y)], fill=(int(r * (1 - 0.6 * k)), int(g * (1 - 0.6 * k)), int(b * (1 - 0.6 * k))))

    font = _font(font_size)
    lines = text.split("\n")
    heights = [draw.textbbox((0, 0), ln, font=font)[3] for ln in lines]
    y = (h - sum(heights) - 10 * (len(lines) - 1)) / 2
    for ln, lh in zip(lines, heights):
        lw = draw.textbbox((0, 0), ln, font=font)[2]
        draw.text(((w - lw) / 2, y), ln, fill="white", font=font)
        y += lh + 10

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def avatar_file(username, color):
    return ContentFile(_gradient_image(color, (256, 256), username[0].upper(), 140), name=f"demo_{username}.jpg")


def portrait_file(prefix, username, color, caption):
    data = _gradient_image(color, (720, 1280), f"{caption}\n\n@{username}", 56)
    return ContentFile(data, name=f"{prefix}_demo_{username}_{random.randint(1000, 9999)}.jpg")


class Command(BaseCommand):
    help = "Create demo friends, chats, snaps, streaks, stories and map locations."

    def add_arguments(self, parser):
        parser.add_argument("--for", dest="targets", action="append", required=True,
                            help="Existing username to connect the demo friends to (repeatable).")
        parser.add_argument("--password", default="demo12345",
                            help="Password for the demo accounts (default: demo12345).")
        parser.add_argument("--reset", action="store_true",
                            help="Delete all demo users (and their data) before seeding.")

    def handle(self, *args, targets, password, reset, **kwargs):
        target_users = []
        for name in targets:
            try:
                target_users.append(SnapUser.objects.get(username=name))
            except SnapUser.DoesNotExist:
                raise CommandError(f"User '{name}' not found. Register it on the site first.")

        if reset:
            n, _ = SnapUser.objects.filter(username__in=DEMO_USERNAMES).delete()
            self.stdout.write(f"Reset: deleted {n} demo objects.")

        friends = {}
        now = timezone.now()

        # 1. Demo friend accounts (avatar + map location)
        for username, color, city, lat, lng, _streak in DEMO_FRIENDS:
            user = self._get_or_create_user(username, color, password)
            # small random offset so pins don't sit exactly on the city centre
            user.latitude = lat + random.uniform(-0.03, 0.03)
            user.longitude = lng + random.uniform(-0.03, 0.03)
            user.last_location_update = now
            user.save(update_fields=["latitude", "longitude", "last_location_update"])
            friends[username] = (user, color)

        pending = [self._get_or_create_user(u, c, password) for u, c in DEMO_PENDING]

        for target in target_users:
            # 2. Friendships + chats + streaks
            for username, color, _city, _lat, _lng, streak in DEMO_FRIENDS:
                friend, _ = friends[username]
                self._make_friends(target, friend)
                self._seed_chat(target, friend, color, CHATS.get(username, []), streak)

            # 3. Incoming pending friend requests
            for user in pending:
                exists = FriendRequest.objects.filter(
                    Q(from_user=user, to_user=target) | Q(from_user=target, to_user=user)
                ).exists()
                if not exists:
                    FriendRequest.objects.create(from_user=user, to_user=target, status="pending")

        # 4. Stories (refresh if expired)
        self._refresh_stories(friends)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready for: {', '.join(targets)}. "
            f"Demo accounts ({', '.join(DEMO_USERNAMES)}) use password '{password}'."
        ))

    # ------------------------------------------------------------------ helpers

    def _get_or_create_user(self, username, color, password):
        user, created = SnapUser.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            f = avatar_file(username, color)
            user.avatar.save(f.name, f, save=False)
            user.save()
        return user

    def _make_friends(self, a, b):
        fr = FriendRequest.objects.filter(Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)).first()
        if fr is None:
            FriendRequest.objects.create(from_user=b, to_user=a, status="accepted")
        elif fr.status != "accepted":
            fr.status = "accepted"
            fr.save(update_fields=["status"])

    def _seed_chat(self, target, friend, color, script, streak):
        u1, u2 = (target, friend) if target.id < friend.id else (friend, target)
        conv, _ = Conversation.objects.get_or_create(user1=u1, user2=u2)

        already = Message.objects.filter(
            Q(sender=target, receiver=friend) | Q(sender=friend, receiver=target)
        ).exists()
        if already or not script:
            return

        now = timezone.now()
        # space the messages out over the last ~day, newest last
        start = now - timedelta(hours=random.randint(2, 20))
        step = (now - start) / (len(script) + 1)
        last_msg, last_preview = None, ""

        for i, (from_friend, text) in enumerate(script):
            sender, receiver = (friend, target) if from_friend else (target, friend)
            if text is None:
                msg = Message(sender=sender, receiver=receiver)
                f = portrait_file("snap", sender.username, color, random.choice(SNAP_CAPTIONS))
                msg.image.save(f.name, f, save=False)
                # snaps YOU sent show as already opened; snaps to you stay "New Snap"
                msg.is_opened = not from_friend
                msg.save()
                last_preview = "📷 Sent a snap"
            else:
                msg = Message.objects.create(sender=sender, receiver=receiver, text_message=text)
                last_preview = text[:50]
            ts = start + step * (i + 1)
            Message.objects.filter(pk=msg.pk).update(created_at=ts)
            last_msg = msg

        conv.last_message = last_msg
        conv.last_message_preview = last_preview
        if streak:
            conv.streak_count = streak
            conv.streak_updated_at = now.date()
            conv.last_snap_user1 = now
            conv.last_snap_user2 = now
        conv.save()
        # chat list is ordered by updated_at — make it match the last message time
        Conversation.objects.filter(pk=conv.pk).update(updated_at=ts)

    def _refresh_stories(self, friends):
        now = timezone.now()
        cutoff = now - timedelta(hours=24)
        for username, captions in STORY_CAPTIONS.items():
            user, color = friends[username]
            # clean up expired demo stories (and their files)
            for old in Story.objects.filter(user=user, created_at__lt=cutoff):
                old.image.delete(save=False)
                old.delete()
            if Story.objects.filter(user=user, created_at__gte=cutoff).exists():
                continue
            for caption in captions:
                story = Story(user=user)
                f = portrait_file("story", username, color, caption)
                story.image.save(f.name, f, save=False)
                story.save()
                Story.objects.filter(pk=story.pk).update(
                    created_at=now - timedelta(minutes=random.randint(10, 600))
                )
