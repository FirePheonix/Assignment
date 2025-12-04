from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from website.models import Brand


class InstagramPostingTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="tester@example.com", password="pass1234"
        )
        # Authenticate test client
        self.client.force_login(self.user)

        # Minimal brand configuration (includes Instagram credentials)
        self.brand = Brand.objects.create(
            name="Test Brand",
            owner=self.user,
            stripe_subscription_status="active",
            instagram_access_token="EAAFAKEVALIDTOKEN",
            instagram_user_id="123456789012345",
            instagram_app_id="999999999999999",
            instagram_app_secret="APPSECRET1234567890",
        )
        # Prepare a tiny in-memory JPEG (not a real image, just enough for
        # tests)
        self.fake_image = SimpleUploadedFile(
            "test.jpg",
            b"\xff\xd8\xff\xe0" + b"fakejpegdata" + b"\xff\xd9",
            content_type="image/jpeg",
        )

    def _mock_head(self, url, *args, **kwargs):
        # Simulate accessible media URL; content-type must be image/*
        resp = MagicMock()
        resp.status_code = 200
        resp.headers = {"content-type": "image/jpeg"}
        return resp

    def _mock_post(self, url, data=None, *args, **kwargs):
        # Container creation returns creation id; publish returns media id
        mock_resp = MagicMock()
        if url.endswith("/media"):
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "CREATION123"}
            mock_resp.text = '{"id": "CREATION123"}'
        elif url.endswith("/media_publish"):
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "987654321"}
            mock_resp.text = '{"id": "987654321"}'
        else:
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"id": "UNKNOWN"}
            mock_resp.text = '{"id": "UNKNOWN"}'
        return mock_resp

    def _mock_get(self, url, params=None, *args, **kwargs):
        mock_resp = MagicMock()
        # Verification & permalink fetch
        if url.endswith("/987654321"):
            # First verify then permalink (fields differ but we can reuse)
            if params and "permalink" in params.get("fields", ""):
                mock_resp.json.return_value = {
                    "permalink": "https://instagram.com/p/abc123/"
                }
            else:
                mock_resp.json.return_value = {
                    "id": "987654321",
                    "permalink": "https://instagram.com/p/abc123/",
                }
            mock_resp.status_code = 200
            mock_resp.text = str(mock_resp.json.return_value)
        else:
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"status_code": "FINISHED"}
            mock_resp.text = '{"status_code": "FINISHED"}'
        return mock_resp

    @patch("website.models.requests.get")
    @patch("website.models.requests.post")
    @patch("website.models.requests.head")
    @patch("website.models.Site.objects.get_current")
    def test_post_to_instagram_success(
        self, mock_site_get_current, mock_head, mock_post, mock_get
    ):
        # Provide fake current site for absolute URL building
        mock_site = MagicMock()
        mock_site.domain = "example.com"
        mock_site_get_current.return_value = mock_site

        mock_head.side_effect = self._mock_head
        mock_post.side_effect = self._mock_post
        mock_get.side_effect = self._mock_get

        # Execute real API endpoint (mocking external Instagram calls)
        response = self.client.post(
            "/api/instagram/post/",
            {
                "brand_id": self.brand.id,
                "content": "Test caption",
            },
            format="multipart",
            **{"wsgi.input": None},  # ensure multipart boundary handling
            FILES={"image": self.fake_image},
        )

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertTrue(data.get("success"), data)
        post_id = data.get("post_id")
        self.assertIsNotNone(post_id)

        # Fetch post from DB and validate posted state
        from website.models import BrandInstagramPost

        created_post = BrandInstagramPost.objects.get(id=post_id)
        self.assertEqual(created_post.status, "posted")
        self.assertIsNotNone(created_post.instagram_id)
        self.assertIsNotNone(created_post.instagram_url)

        # Ensure network interactions happened as expected
        self.assertGreaterEqual(
            mock_post.call_count,
            2,
            "Expected at least two POST calls (container + publish)",
        )
        mock_head.assert_called()  # Media accessibility check

        # Ensure the correct token was sent in initial container creation call
        first_post_call = None
        for call in mock_post.call_args_list:
            if call.args and call.args[0].endswith("/media"):
                first_post_call = call
                break
        self.assertIsNotNone(
            first_post_call,
            "Did not call media container creation endpoint",
        )
        sent_data = first_post_call.kwargs.get("data") or (
            len(first_post_call.args) > 1 and first_post_call.args[1] or {}
        )
        self.assertEqual(
            sent_data.get("access_token"), self.brand.instagram_access_token
        )
