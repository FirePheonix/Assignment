from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()


class APIAuthTestCase(TestCase):
    """Test suite for API authentication endpoints"""

    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.test_user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123!",
            "password2": "testpass123!",
        }
        self.login_data = {"email": "test@example.com", "password": "testpass123!"}

    def test_user_registration(self):
        """Test user registration via API"""
        url = reverse("rest_register")

        response = self.client.post(url, self.test_user_data, format="json")

        # Registration can return either 201 Created or 204 No Content
        # depending on the configuration (e.g., email verification settings)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT]
        )

        # If response is 201, check for response data
        if response.status_code == status.HTTP_201_CREATED:
            self.assertIsNotNone(response.data)

        # Verify user was created regardless of response code
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123!"))

    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data"""
        url = reverse("rest_register")

        # Missing password confirmation
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "testpass123!",
        }

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password2", response.data)

    def test_user_login(self):
        """Test user login via API"""
        # Create user first
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123!"
        )

        url = reverse("rest_login")

        response = self.client.post(url, self.login_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # dj_rest_auth returns token as 'key'
        self.assertIn("key", response.data)

        # Verify token is valid
        token = response.data["key"]
        self.assertTrue(Token.objects.filter(key=token).exists())

    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        url = reverse("rest_login")

        invalid_data = {"email": "nonexistent@test.com", "password": "wrongpassword"}

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_user_logout(self):
        """Test user logout via API"""
        # Create user and login
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123!"
        )
        token = Token.objects.create(user=user)

        # Set authentication
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        url = reverse("rest_logout")

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify token is deleted
        self.assertFalse(Token.objects.filter(key=token.key).exists())

    def test_logout_idempotent_behavior(self):
        """Test that logout is idempotent (safe to call without authentication)"""
        url = reverse("rest_logout")

        response = self.client.post(url)

        # dj-rest-auth logout endpoint returns 200 even for unauthenticated requests
        # This is by design to make logout idempotent
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIUserProfileTestCase(TestCase):
    """Test suite for API user profile endpoints"""

    def setUp(self):
        """Set up test data and authenticated client"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123!",
            first_name="Test",
            last_name="User",
            bio="Test user bio",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

    def test_get_user_profile(self):
        """Test getting user profile via API"""
        url = reverse("website:user_profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify profile data
        data = response.data
        self.assertEqual(data["id"], self.user.id)
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertEqual(data["bio"], "Test user bio")
        self.assertIsNone(data["profile_picture"])  # No image uploaded
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_get_user_profile_requires_authentication(self):
        """Test that getting profile requires authentication"""
        # Remove authentication
        self.client.credentials()

        url = reverse("website:user_profile")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """Test updating user profile via API"""
        url = reverse("website:update_user_profile")

        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "bio": "Updated bio content",
        }

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify data was updated
        data = response.data
        self.assertEqual(data["first_name"], "Updated")
        self.assertEqual(data["last_name"], "Name")
        self.assertEqual(data["bio"], "Updated bio content")

        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.bio, "Updated bio content")

    def test_update_user_profile_partial(self):
        """Test partial update of user profile"""
        url = reverse("website:update_user_profile")

        update_data = {"bio": "Only updating bio"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify only bio was updated
        data = response.data
        self.assertEqual(data["bio"], "Only updating bio")
        # Should remain unchanged
        self.assertEqual(data["first_name"], "Test")
        # Should remain unchanged
        self.assertEqual(data["last_name"], "User")

    def test_update_user_profile_readonly_fields(self):
        """Test that read-only fields cannot be updated"""
        url = reverse("website:update_user_profile")

        update_data = {
            "id": 999,
            "email": "hacker@example.com",
            "username": "hacker",
            "first_name": "Legitimate",
            "bio": "Legitimate update",
        }

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify read-only fields were not updated
        data = response.data
        self.assertEqual(data["id"], self.user.id)  # Should remain unchanged
        self.assertEqual(data["email"], "test@example.com")  # Should remain unchanged
        self.assertEqual(data["username"], "testuser")  # Should remain unchanged

        # Verify allowed fields were updated
        self.assertEqual(data["first_name"], "Legitimate")
        self.assertEqual(data["bio"], "Legitimate update")

    def test_update_user_profile_requires_authentication(self):
        """Test that updating profile requires authentication"""
        # Remove authentication
        self.client.credentials()

        url = reverse("website:update_user_profile")

        update_data = {"first_name": "Hacker"}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile_invalid_data(self):
        """Test updating profile with invalid data"""
        url = reverse("website:update_user_profile")

        # Bio too long (max 500 characters)
        update_data = {"bio": "x" * 501}

        response = self.client.patch(url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bio", response.data)


class APIIntegrationTestCase(TestCase):
    """Integration tests for complete API workflows"""

    def setUp(self):
        """Set up test client"""
        self.client = APIClient()

    def test_complete_user_flow(self):
        """Test complete user registration -> login -> profile update -> logout flow"""
        # 1. Register user
        register_data = {
            "username": "flowtest",
            "email": "flow@example.com",
            "password1": "flowpass123!",
            "password2": "flowpass123!",
        }

        response = self.client.post(
            reverse("rest_register"), register_data, format="json"
        )
        # Registration can return either 201 Created or 204 No Content
        # depending on the configuration (e.g., email verification settings)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT]
        )

        # Login to get token (since registration may not return token)
        login_data = {"email": "flow@example.com", "password": "flowpass123!"}
        response = self.client.post(reverse("rest_login"), login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["key"]

        # 2. Use token to access protected endpoints
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

        # 3. Get profile
        response = self.client.get(reverse("website:user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "flowtest")

        # 4. Update profile
        update_data = {
            "first_name": "Flow",
            "last_name": "Test",
            "bio": "Complete flow test user",
        }

        response = self.client.patch(
            reverse("website:update_user_profile"), update_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Flow")

        # 5. Logout
        response = self.client.post(reverse("rest_logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. Verify token is invalidated
        response = self.client.get(reverse("website:user_profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_and_profile_flow(self):
        """Test login with existing user and profile operations"""
        # Create user manually
        User.objects.create_user(
            username="logintest", email="login@example.com", password="loginpass123!"
        )

        # 1. Login
        login_data = {"email": "login@example.com", "password": "loginpass123!"}

        response = self.client.post(reverse("rest_login"), login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Get token
        token = response.data["key"]
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)

        # 2. Get profile
        response = self.client.get(reverse("website:user_profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "logintest")

        # 3. Update profile
        update_data = {"bio": "Updated via login flow"}

        response = self.client.patch(
            reverse("website:update_user_profile"), update_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Updated via login flow")
