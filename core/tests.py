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

    def test_upload_story_valid_and_invalid(self):
        self.assertEqual(self.client.post("/upload-story/", {"image": make_image()}).status_code, 200)
        bad = SimpleUploadedFile("x.jpg", b"not an image", content_type="image/jpeg")
        self.assertEqual(self.client.post("/upload-story/", {"image": bad}).status_code, 400)
        self.assertEqual(Story.objects.count(), 1)


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
