from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class LoginRedirectionFixTest(TestCase):
    """
    Simple test to verify that the login redirection loop issue is fixed.
    This test focuses specifically on the core issue reported.
    """

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123!",
            is_staff=True,
            is_superuser=True,
        )
        # Ensure email is verified for allauth
        from allauth.account.models import EmailAddress

        EmailAddress.objects.create(
            user=self.test_user, email="test@example.com", verified=True, primary=True
        )

        self.login_url = reverse("account_login")
        self.landing_url = reverse("website:landing")
        self.admin_url = f"/{settings.ADMIN_URL}/"

    def test_login_does_not_redirect_back_to_login(self):
        """Test that login doesn't redirect back to login page - this is the main bug fix"""
        response = self.client.post(
            self.login_url, {"login": "test@example.com", "password": "testpass123!"}
        )

        # Should redirect to landing page, NOT back to login
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.landing_url)

        # Follow the redirect to make sure it works
        follow_response = self.client.post(
            self.login_url,
            {"login": "test@example.com", "password": "testpass123!"},
            follow=True,
        )

        # Should end up on landing page
        self.assertEqual(follow_response.status_code, 200)
        # Should NOT be the login page
        self.assertNotIn("Sign In", follow_response.content.decode())

    def test_authenticated_user_can_access_protected_pages(self):
        """Test that authenticated users can access protected pages without being redirected to login"""
        # Login user
        login_response = self.client.post(
            self.login_url, {"login": "test@example.com", "password": "testpass123!"}
        )

        # Should redirect to landing page
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, self.landing_url)

        # Now try to access the landing page directly
        landing_response = self.client.get(self.landing_url)
        self.assertEqual(landing_response.status_code, 200)
        # Should NOT be redirected back to login
        self.assertNotIn("Sign In", landing_response.content.decode())

    def test_admin_dashboard_accessible_after_login(self):
        """Test that admin dashboard is accessible after login"""
        # Login user
        self.client.login(username="testuser", password="testpass123!")

        # Try to access admin dashboard
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        # Should not be redirected to login
        self.assertNotIn("Sign In", response.content.decode())

    def test_session_persists_between_requests(self):
        """Test that session persists between requests (no login loop)"""
        # Login user
        self.client.login(username="testuser", password="testpass123!")

        # Make multiple requests to protected pages
        for _ in range(3):
            response = self.client.get(self.landing_url)
            self.assertEqual(response.status_code, 200)
            # Should not be redirected to login on any request
            self.assertNotIn("Sign In", response.content.decode())

    def test_invalid_login_shows_error_not_redirect_loop(self):
        """Test that invalid login shows error message instead of redirect loop"""
        response = self.client.post(
            self.login_url, {"login": "test@example.com", "password": "wrongpassword"}
        )

        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)
        # Should show error message
        self.assertIn("not correct", response.content.decode())

    def test_unauthenticated_user_properly_redirected(self):
        """Test that unauthenticated users are properly redirected to login"""
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

        # Follow the redirect
        follow_response = self.client.get(self.landing_url, follow=True)
        self.assertEqual(follow_response.status_code, 200)
        # Should show login page
        self.assertIn("Sign In", follow_response.content.decode())

    def test_logout_and_login_again_works(self):
        """Test that logout and login again works without issues"""
        # Login user
        self.client.login(username="testuser", password="testpass123!")

        # Verify user is logged in
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 200)

        # Logout
        logout_response = self.client.post(reverse("account_logout"))
        self.assertEqual(logout_response.status_code, 302)

        # Try to access protected page - should be redirected to login
        response = self.client.get(self.landing_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

        # Login again
        login_response = self.client.post(
            self.login_url, {"login": "test@example.com", "password": "testpass123!"}
        )

        # Should redirect to landing page again
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, self.landing_url)
