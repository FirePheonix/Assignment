from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import ProfileImpression, Task, Brand, BrandTweet
from organizations.models import Organization
import json

User = get_user_model()


class HomepageTest(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get(reverse("website:index"))
        self.assertEqual(response.status_code, 200)


class ProfileImpressionModelTest(TestCase):
    def setUp(self):
        self.profile_user = User.objects.create_user(
            username="profileuser", email="profile@test.com", password="testpass123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", email="viewer@test.com", password="testpass123"
        )

    def test_profile_impression_creation(self):
        """Test creating a profile impression"""
        impression = ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=self.viewer,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
            country="US",
            city="New York",
        )

        self.assertEqual(impression.profile_user, self.profile_user)
        self.assertEqual(impression.viewer, self.viewer)
        self.assertEqual(impression.ip_address, "192.168.1.1")
        self.assertEqual(impression.country, "US")
        self.assertTrue(impression.timestamp)

    def test_anonymous_profile_impression(self):
        """Test creating a profile impression for anonymous viewer"""
        impression = ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=None,  # Anonymous viewer
            ip_address="192.168.1.2",
            user_agent="Mozilla/5.0 Test Browser",
            country="CA",
            city="Toronto",
        )

        self.assertEqual(impression.profile_user, self.profile_user)
        self.assertIsNone(impression.viewer)
        self.assertEqual(impression.ip_address, "192.168.1.2")

    def test_user_impressions_count_update(self):
        """Test that impressions_count is updated when ProfileImpression is created"""
        initial_count = self.profile_user.impressions_count

        # Create multiple impressions
        ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=self.viewer,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=None,
            ip_address="192.168.1.2",
            user_agent="Test Browser",
        )

        # Refresh from database
        self.profile_user.refresh_from_db()

        # Check that count increased by 2
        self.assertEqual(self.profile_user.impressions_count, initial_count + 2)


class ProfileImpressionAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.profile_user = User.objects.create_user(
            username="profileuser", email="profile@test.com", password="testpass123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", email="viewer@test.com", password="testpass123"
        )

        # Create tokens for authentication
        self.profile_token = Token.objects.create(user=self.profile_user)
        self.viewer_token = Token.objects.create(user=self.viewer)

    def test_track_profile_impression_authenticated(self):
        """Test tracking profile impression with authenticated user"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.viewer_token.key)

        url = reverse(
            "website:track_profile_impression", kwargs={"user_id": self.profile_user.id}
        )

        # Set up request headers for testing
        response = self.client.post(
            url,
            data={"country": "US", "city": "New York"},
            HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
            REMOTE_ADDR="192.168.1.1",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], "Profile impression tracked successfully")
        self.assertEqual(data["impressions_count"], 1)

        # Check database
        impression = ProfileImpression.objects.get(profile_user=self.profile_user)
        self.assertEqual(impression.viewer, self.viewer)
        self.assertEqual(impression.ip_address, "192.168.1.1")
        self.assertEqual(impression.country, "US")
        self.assertEqual(impression.city, "New York")

        # Check user impressions count updated
        self.profile_user.refresh_from_db()
        self.assertEqual(self.profile_user.impressions_count, 1)

    def test_track_profile_impression_unauthenticated(self):
        """Test tracking profile impression without authentication"""
        url = reverse(
            "website:track_profile_impression", kwargs={"user_id": self.profile_user.id}
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_track_profile_impression_nonexistent_user(self):
        """Test tracking impression for non-existent user"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.viewer_token.key)

        url = reverse("website:track_profile_impression", kwargs={"user_id": 99999})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_track_own_profile_impression(self):
        """Test tracking impression on own profile"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.profile_token.key)

        url = reverse(
            "website:track_profile_impression", kwargs={"user_id": self.profile_user.id}
        )

        response = self.client.post(url)

        # Should return 200 with a message that self-impression is not tracked
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data
        data = response.json()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], "Self-impression not tracked")
        self.assertEqual(
            data["impressions_count"], 0
        )  # Should remain 0 for self-impressions

    def test_user_detail_includes_impressions_count(self):
        """Test that user detail API includes impressions_count"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.viewer_token.key)

        # Create some impressions first
        ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=self.viewer,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        url = reverse("website:user_detail", kwargs={"user_id": self.profile_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("impressions_count", data)
        self.assertEqual(data["impressions_count"], 1)

    def test_users_feed_includes_impressions_count(self):
        """Test that users feed API includes impressions_count"""
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.viewer_token.key)

        # Create some impressions
        ProfileImpression.objects.create(
            profile_user=self.profile_user,
            viewer=self.viewer,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        url = reverse("website:users_feed")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("users", data)

        # Find our profile user in the feed
        profile_user_data = next(
            (user for user in data["users"] if user["id"] == self.profile_user.id), None
        )

        self.assertIsNotNone(profile_user_data)
        self.assertIn("impressions_count", profile_user_data)
        self.assertEqual(profile_user_data["impressions_count"], 1)


class ProfileImpressionIntegrationTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # Create multiple test users
        self.users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}", email=f"user{i}@test.com", password="testpass123"
            )
            Token.objects.create(user=user)
            self.users.append(user)

    def test_multiple_users_viewing_profile(self):
        """Test multiple users viewing the same profile"""
        target_user = self.users[0]

        # Multiple users view the target user's profile
        for i, viewer in enumerate(self.users[1:], 1):
            self.client.credentials(HTTP_AUTHORIZATION=f"Token {viewer.auth_token.key}")

            url = reverse(
                "website:track_profile_impression", kwargs={"user_id": target_user.id}
            )

            # Set up request headers for testing
            response = self.client.post(
                url,
                data={"country": "US", "city": "New York"},
                HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
                REMOTE_ADDR=f"192.168.1.{i}",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check final impressions count
        target_user.refresh_from_db()
        self.assertEqual(target_user.impressions_count, 2)

        # Check that all impressions are recorded
        impressions = ProfileImpression.objects.filter(profile_user=target_user)
        self.assertEqual(impressions.count(), 2)

    def test_same_user_multiple_views(self):
        """Test same user viewing profile multiple times (should create multiple impressions)"""
        target_user = self.users[0]
        viewer = self.users[1]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {viewer.auth_token.key}")
        url = reverse(
            "website:track_profile_impression", kwargs={"user_id": target_user.id}
        )

        # View profile multiple times (only first should be tracked due to spam prevention)
        for i in range(3):
            response = self.client.post(
                url,
                data={"country": "US", "city": "New York"},
                HTTP_USER_AGENT="Mozilla/5.0 Test Browser",
                REMOTE_ADDR="192.168.1.1",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check impressions count (should be 1 due to spam prevention)
        target_user.refresh_from_db()
        self.assertEqual(target_user.impressions_count, 1)

        # Check that only one view is recorded (due to spam prevention)
        impressions = ProfileImpression.objects.filter(
            profile_user=target_user, viewer=viewer
        )
        self.assertEqual(impressions.count(), 1)

    def test_impression_analytics_data(self):
        """Test that impression analytics data is properly recorded"""
        target_user = self.users[0]
        viewer = self.users[1]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {viewer.auth_token.key}")
        url = reverse(
            "website:track_profile_impression", kwargs={"user_id": target_user.id}
        )

        test_ip = "203.0.113.1"
        test_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"

        # Set up request with analytics data
        response = self.client.post(
            url,
            data={"country": "Canada", "city": "Vancouver"},
            HTTP_USER_AGENT=test_user_agent,
            REMOTE_ADDR=test_ip,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that analytics data is properly stored
        impression = ProfileImpression.objects.get(
            profile_user=target_user, viewer=viewer
        )

        self.assertEqual(impression.ip_address, test_ip)
        self.assertEqual(impression.user_agent, test_user_agent)
        self.assertEqual(impression.country, "Canada")
        self.assertEqual(impression.city, "Vancouver")


class UserModelImpressionTest(TestCase):
    """Test the User model's impression-related functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )

    def test_initial_impressions_count(self):
        """Test that new users start with 0 impressions"""
        self.assertEqual(self.user.impressions_count, 0)

    def test_impressions_count_field_type(self):
        """Test that impressions_count is an integer field"""
        field = User._meta.get_field("impressions_count")
        self.assertEqual(field.get_internal_type(), "PositiveIntegerField")
        self.assertEqual(field.default, 0)


class TaskCreationTest(TestCase):
    """Test task creation functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_task_creation_basic(self):
        """Test basic task creation works"""
        task_data = {
            "title": "Test Task",
            "description": "This is a test task description",
            "category": "POST",
            "genre": "BEAUTY",
            "incentive_type": "NONE",
        }

        response = self.client.post(
            reverse("website:task_create"),
            data=task_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(
            response_data.get("success"),
            f"Task creation failed: {response_data.get('error')}",
        )

        # Verify task was created in database
        task = Task.objects.get(id=response_data.get("task_id"))
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.brand, self.user)
        self.assertEqual(task.category, "POST")
        self.assertEqual(task.genre, "BEAUTY")
        self.assertEqual(task.incentive_type, "NONE")

    def test_add_twitter_post_to_queue(self):
        """Test adding a Twitter post to the Twitter queue"""
        from django.utils import timezone

        # Create organization
        organization = Organization.objects.create(
            name="Test Organization", slug="test-org"
        )

        # Create brand associated with organization
        brand = Brand.objects.create(
            name="Test Brand",
            slug="test-brand",
            url="https://testbrand.com",
            description="A test brand",
            owner=self.user,
            organization=organization,
        )

        # Test creating a brand tweet directly (simpler approach)
        tweet = BrandTweet.objects.create(
            brand=brand,
            content="This is a test tweet for the queue",
            status="draft",
            scheduled_for=timezone.now() + timezone.timedelta(hours=1),
        )

        # Verify tweet was created successfully
        self.assertEqual(tweet.content, "This is a test tweet for the queue")
        self.assertEqual(tweet.brand, brand)
        self.assertEqual(tweet.status, "draft")
        self.assertIsNotNone(tweet.scheduled_for)

        # Verify it's in the database
        saved_tweet = BrandTweet.objects.get(id=tweet.id)
        self.assertEqual(saved_tweet.content, "This is a test tweet for the queue")
        self.assertEqual(saved_tweet.brand, brand)
