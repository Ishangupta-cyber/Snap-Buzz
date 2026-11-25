"""
Demo data for Snap Buzz — shared by the `seed_demo` command and the
"Try the demo" button (one fresh guest account per visitor).

Demo FRIENDS (aarav, priya, ...) are shared and permanent.
Each target account (yours, or a throwaway guest) gets its OWN chats with them,
so visitors never see each other's activity.
"""

import io
import random
import secrets
from datetime import timedelta

from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone
from PIL import Image, ImageColor, ImageDraw, ImageFont

from core.models import Conversation, FriendRequest, Message, SnapUser, Story

DEMO_FRIEND_PASSWORD = "demo12345"

# username, colour, city, lat, lng, streak
DEMO_FRIENDS = [
    ("aarav", "#8b5cf6", "Delhi", 28.6139, 77.2090, 12),
    ("priya", "#ec4899", "Mumbai", 19.0760, 72.8777, 27),
    ("rohan", "#06b6d4", "Bengaluru", 12.9716, 77.5946, 5),
    ("ananya", "#f59e0b", "Jaipur", 26.9124, 75.7873, 0),
    ("kabir", "#10b981", "Pune", 18.5204, 73.8567, 3),
    ("isha", "#ef4444", "Kolkata", 22.5726, 88.3639, 0),
]

# These users send the target a friend request (Friend Requests page)
DEMO_PENDING = [
    ("meera", "#6366f1"),
    ("vihaan", "#14b8a6"),
]

DEMO_USERNAMES = [u[0] for u in DEMO_FRIENDS] + [u[0] for u in DEMO_PENDING]

# (from_friend, text) — text None => a snap
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


# --------------------------------------------------------------------------- images

def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def gradient_image(color, size, text, font_size):
    """Vertical gradient with centred white text -> JPEG bytes."""
    w, h = size
    r, g, b = ImageColor.getrgb(color)
    # top = colour, fading to 40% brightness at the bottom (built in C, no per-line loop)
    mask = Image.linear_gradient("L").resize(size)
    dark = Image.new("RGB", size, (int(r * 0.4), int(g * 0.4), int(b * 0.4)))
    img = Image.composite(dark, Image.new("RGB", size, color), mask)
    draw = ImageDraw.Draw(img)

    font = _font(font_size)
    lines = text.split("\n")
    heights = [max(draw.textbbox((0, 0), ln or " ", font=font)[3], font_size // 2) for ln in lines]
    y = (h - sum(heights) - 10 * (len(lines) - 1)) / 2
    for ln, lh in zip(lines, heights):
        lw = draw.textbbox((0, 0), ln, font=font)[2] if ln else 0
        draw.text(((w - lw) / 2, y), ln, fill="white", font=font)
        y += lh + 10

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _avatar_file(label, color, name):
    return ContentFile(gradient_image(color, (256, 256), label[0].upper(), 140), name=f"demo_{name}.jpg")


def _portrait_file(prefix, username, color, caption):
    data = gradient_image(color, (720, 1280), f"{caption}\n\n@{username}", 56)
    return ContentFile(data, name=f"{prefix}_demo_{username}_{random.randint(1000, 9999)}.jpg")


# --------------------------------------------------------------------------- users

def _get_or_create_user(username, color, password):
    user, created = SnapUser.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        f = _avatar_file(username, color, username)
        user.avatar.save(f.name, f, save=False)
        user.save()
    return user


def ensure_demo_friends(password=DEMO_FRIEND_PASSWORD):
    """Create/refresh the shared demo friends. Returns {username: (user, colour)}."""
    now = timezone.now()
    friends = {}
    for username, color, _city, lat, lng, _streak in DEMO_FRIENDS:
        user = _get_or_create_user(username, color, password)
        if user.latitude is None:
            # small random offset so pins don't sit exactly on the city centre
            user.latitude = lat + random.uniform(-0.03, 0.03)
            user.longitude = lng + random.uniform(-0.03, 0.03)
        user.last_location_update = now
        user.save(update_fields=["latitude", "longitude", "last_location_update"])
        friends[username] = (user, color)
    for username, color in DEMO_PENDING:
        _get_or_create_user(username, color, password)
    return friends


def delete_demo_users():
    users = SnapUser.objects.filter(username__in=DEMO_USERNAMES)
    for user in users:
        delete_user_files(user)
    return users.delete()[0]


def delete_user_files(user):
    """Remove uploaded files tied to a user (deleting rows doesn't delete files)."""
    for msg in Message.objects.filter(Q(sender=user) | Q(receiver=user)).exclude(image=""):
        msg.image.delete(save=False)
    for story in Story.objects.filter(user=user):
        story.image.delete(save=False)
    if user.avatar and user.avatar.name.startswith("avatar/demo_"):
        user.avatar.delete(save=False)


# --------------------------------------------------------------------------- seeding

def _make_friends(a, b):
    fr = FriendRequest.objects.filter(Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)).first()
    if fr is None:
        FriendRequest.objects.create(from_user=b, to_user=a, status="accepted")
    elif fr.status != "accepted":
        fr.status = "accepted"
        fr.save(update_fields=["status"])


def _seed_chat(target, friend, color, script, streak):
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
    last_msg, last_preview, ts = None, "", now

    for i, (from_friend, text) in enumerate(script):
        sender, receiver = (friend, target) if from_friend else (target, friend)
        if text is None:
            msg = Message(sender=sender, receiver=receiver)
            f = _portrait_file("snap", sender.username, color, random.choice(SNAP_CAPTIONS))
            msg.image.save(f.name, f, save=False)
            # snaps the target sent show as opened; snaps TO the target stay "New Snap"
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


def seed_for(target, friends):
    """Connect `target` to the demo friends with chats, snaps, streaks and pending requests."""
    for username, color, _city, _lat, _lng, streak in DEMO_FRIENDS:
        friend, _ = friends[username]
        _make_friends(target, friend)
        _seed_chat(target, friend, color, CHATS.get(username, []), streak)

    for username, _color in DEMO_PENDING:
        user = SnapUser.objects.get(username=username)
        exists = FriendRequest.objects.filter(
            Q(from_user=user, to_user=target) | Q(from_user=target, to_user=user)
        ).exists()
        if not exists:
            FriendRequest.objects.create(from_user=user, to_user=target, status="pending")


def refresh_stories(friends):
    """Stories expire after 24h — delete expired demo ones and post fresh ones."""
    now = timezone.now()
    cutoff = now - timedelta(hours=24)
    for username, captions in STORY_CAPTIONS.items():
        user, color = friends[username]
        for old in Story.objects.filter(user=user, created_at__lt=cutoff):
            old.image.delete(save=False)
            old.delete()
        if Story.objects.filter(user=user, created_at__gte=cutoff).exists():
            continue
        for caption in captions:
            story = Story(user=user)
            f = _portrait_file("story", username, color, caption)
            story.image.save(f.name, f, save=False)
            story.save()
            Story.objects.filter(pk=story.pk).update(
                created_at=now - timedelta(minutes=random.randint(10, 600))
            )


# --------------------------------------------------------------------------- guests

def create_guest():
    """A brand-new throwaway account pre-filled with demo data (for 'Try the demo')."""
    friends = ensure_demo_friends()
    refresh_stories(friends)

    while True:
        username = f"guest_{secrets.token_hex(3)}"
        if not SnapUser.objects.filter(username=username).exists():
            break

    guest = SnapUser(username=username, is_demo_guest=True)
    guest.set_unusable_password()  # only reachable through the demo button
    f = _avatar_file("G", "#334155", username)
    guest.avatar.save(f.name, f, save=False)
    guest.save()

    seed_for(guest, friends)
    return guest


def cleanup_guests(older_than_hours=24):
    cutoff = timezone.now() - timedelta(hours=older_than_hours)
    guests = SnapUser.objects.filter(is_demo_guest=True, date_joined__lt=cutoff)
    for guest in guests:
        delete_user_files(guest)
    return guests.delete()[0]
