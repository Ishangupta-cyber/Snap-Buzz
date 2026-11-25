import io
import shutil
import tempfile

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, TransactionTestCase, override_settings
from PIL import Image

from core.models import FriendRequest, Message, SnapUser, Story

TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name="snap.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, format="JPEG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/jpeg")


def make_users():
    alice = SnapUser.objects.create_user("alice", password="pass12345!")
    bob = SnapUser.objects.create_user("bob", password="pass12345!")
    eve = SnapUser.objects.create_user("eve", password="pass12345!")
    FriendRequest.objects.create(from_user=alice, to_user=bob, status="accepted")
    return alice, bob, eve


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.alice, self.bob, self.eve = make_users()
        self.client.force_login(self.alice)

    def test_search_marks_existing_friend_as_friend(self):
        resp = self.client.get("/search/", {"username": "bob"})
        self.assertIn(self.bob.id, resp.context["unique_friends"])
        self.assertContains(resp, "Friends")
        self.assertNotContains(resp, f"/send-invite/{self.bob.id}")

    def test_search_shows_add_for_non_friend(self):
        resp = self.client.get("/search/", {"username": "eve"})
        self.assertContains(resp, f"/send-invite/{self.eve.id}")

    def test_send_invite_unknown_user_is_404(self):
        self.assertEqual(self.client.post("/send-invite/9999").status_code, 404)

    def test_send_text_message_to_friend(self):
        resp = self.client.post(f"/send-message/{self.bob.id}", {"content": "hi"})
        self.assertEqual(resp.json()["status"], "success")
        self.assertTrue(Message.objects.filter(sender=self.alice, text_message="hi").exists())

    def test_send_message_to_non_friend_rejected(self):
        resp = self.client.post(f"/send-message/{self.eve.id}", {"content": "hi"})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Message.objects.exists())

    def test_send_valid_snap(self):
        resp = self.client.post(f"/send-message/{self.bob.id}", {"image": make_image()})
        self.assertEqual(resp.json()["status"], "success")

    def test_send_fake_image_rejected(self):
        bad = SimpleUploadedFile("evil.html", b"<script>alert(1)</script>", content_type="image/jpeg")
        resp = self.client.post(f"/send-message/{self.bob.id}", {"image": bad})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Message.objects.exists())

    def test_spotlight_empty_state(self):
        with override_settings(MEDIA_ROOT=tempfile.mkdtemp()):
            self.assertContains(self.client.get("/spotlight/"), "No Spotlight videos yet")

    def test_spotlight_lists_videos_muted_for_autoplay(self):
        import os
        media = tempfile.mkdtemp()
        os.makedirs(os.path.join(media, "stories"))
        for name in ("b.mp4", "a.MP4", "story.jpg"):
            open(os.path.join(media, "stories", name), "wb").close()
        with override_settings(MEDIA_ROOT=media):
            resp = self.client.get("/spotlight/")
        self.assertEqual(resp.context["videos"], ["/media/stories/a.MP4", "/media/stories/b.mp4"])
        import re
        video_tags = re.findall(r"<video[^>]*>", resp.content.decode())
        self.assertEqual(len(video_tags), 2)
        self.assertTrue(all(re.search(r"\bmuted\b", tag) for tag in video_tags))
        shutil.rmtree(media, ignore_errors=True)

    def test_upload_story_valid_and_invalid(self):
        self.assertEqual(self.client.post("/upload-story/", {"image": make_image()}).status_code, 200)
        bad = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
        self.assertEqual(self.client.post("/upload-story/", {"image": bad}).status_code, 400)
        self.assertEqual(Story.objects.count(), 1)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SeedDemoTests(TestCase):
    def test_seed_creates_demo_data_and_is_idempotent(self):
        from django.core.management import call_command
        from core.models import Conversation

        me = SnapUser.objects.create_user("ishan", password="pass12345!")
        call_command("seed_demo", "--for", "ishan", stdout=io.StringIO())

        friends = FriendRequest.objects.filter(to_user=me, status="accepted").count()
        pending = FriendRequest.objects.filter(to_user=me, status="pending").count()
        msgs = Message.objects.count()
        self.assertEqual(friends, 6)
        self.assertEqual(pending, 2)
        self.assertGreater(msgs, 15)
        self.assertTrue(Message.objects.filter(receiver=me, is_opened=False).exclude(image="").exists())
        self.assertGreater(Story.objects.count(), 0)
        self.assertTrue(Conversation.objects.filter(streak_count=27).exists())
        self.assertEqual(SnapUser.objects.filter(latitude__isnull=False).count(), 6)

        # Map page receives the friends' locations
        self.client.force_login(me)
        self.assertContains(self.client.get("/map/"), "priya")

        # Re-running must not duplicate anything
        stories = Story.objects.count()
        call_command("seed_demo", "--for", "ishan", stdout=io.StringIO())
        self.assertEqual(Message.objects.count(), msgs)
        self.assertEqual(Story.objects.count(), stories)

        # Reset wipes and re-creates cleanly
        call_command("seed_demo", "--for", "ishan", "--reset", stdout=io.StringIO())
        self.assertEqual(FriendRequest.objects.filter(to_user=me, status="accepted").count(), 6)
        self.assertEqual(Message.objects.count(), msgs)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DemoLoginTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_login_page_has_demo_button(self):
        self.assertContains(self.client.get("/login/"), 'action="/demo/"')

    def test_demo_button_logs_in_fresh_guest_with_data(self):
        resp = self.client.post("/demo/")
        self.assertRedirects(resp, "/")
        guest = SnapUser.objects.get(is_demo_guest=True)
        self.assertTrue(guest.username.startswith("guest_"))
        self.assertFalse(guest.has_usable_password())
        self.assertEqual(FriendRequest.objects.filter(to_user=guest, status="accepted").count(), 6)

        home = self.client.get("/")
        self.assertContains(home, "priya")
        self.assertContains(home, "🔥")

    def test_each_visitor_gets_isolated_data(self):
        self.client.post("/demo/")
        first = SnapUser.objects.get(is_demo_guest=True)
        snap = Message.objects.filter(receiver=first, is_opened=False).exclude(image="").first()
        self.client.post(f"/mark-snap-opened/{snap.id}")  # visitor 1 opens a snap

        other = self.client_class()
        other.post("/demo/")
        second = SnapUser.objects.filter(is_demo_guest=True).exclude(pk=first.pk).get()
        # visitor 2 still has all their snaps unopened
        self.assertFalse(Message.objects.filter(receiver=second, is_opened=True).exists())

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get("/demo/").status_code, 405)

    def test_rate_limited_per_ip(self):
        from core.views.auth_views import DEMO_LOGINS_PER_IP_PER_HOUR
        for _ in range(DEMO_LOGINS_PER_IP_PER_HOUR):
            self.client_class().post("/demo/")
        resp = self.client_class().post("/demo/")
        self.assertEqual(resp.status_code, 429)

    def test_cleanup_removes_only_old_guests(self):
        from datetime import timedelta
        from django.core.management import call_command
        from django.utils import timezone

        self.client.post("/demo/")
        self.client_class().post("/demo/")
        real = SnapUser.objects.create_user("realuser", password="pass12345!")
        old = SnapUser.objects.filter(is_demo_guest=True).first()
        SnapUser.objects.filter(pk=old.pk).update(date_joined=timezone.now() - timedelta(hours=25))

        call_command("cleanup_guests", stdout=io.StringIO())
        self.assertFalse(SnapUser.objects.filter(pk=old.pk).exists())
        self.assertEqual(SnapUser.objects.filter(is_demo_guest=True).count(), 1)
        self.assertTrue(SnapUser.objects.filter(pk=real.pk).exists())
        self.assertTrue(SnapUser.objects.filter(username="priya").exists())  # shared friends kept


class ConsumerTests(TransactionTestCase):
    def setUp(self):
        self.alice, self.bob, self.eve = make_users()

    def _connect(self, user, friend_id):
        from snap.asgi import application  # noqa: F401  (ensures settings loaded)
        from core.consumers import ChatConsumer

        async def run():
            comm = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{friend_id}/")
            comm.scope["user"] = user
            comm.scope["url_route"] = {"kwargs": {"friend_id": friend_id}}
            connected, _ = await comm.connect()
            await comm.disconnect()
            return connected

        return async_to_sync(run)()

    def test_friend_can_connect(self):
        self.assertTrue(self._connect(self.alice, self.bob.id))

    def test_non_friend_cannot_connect(self):
        self.assertFalse(self._connect(self.eve, self.alice.id))
