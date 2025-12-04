from django.test import TestCase
from django.urls import reverse


class AuthStylingTest(TestCase):
    """
    Tests to ensure that the django-allauth templates are being
    correctly overridden and styled.
    """

    def test_login_page_has_custom_styled_container(self):
        """
        Verifies that the login page is rendered with our custom layout.

        It checks for the presence of the specific container class that
        should be wrapping the form.
        """
        login_url = reverse("account_login")
        response = self.client.get(login_url)

        self.assertEqual(
            response.status_code, 200, "Login page did not return a 200 OK."
        )

        # Check for the presence of our custom auth-container class
        self.assertContains(
            response,
            'class="auth-container"',
            count=1,
            status_code=200,
            msg_prefix=("Auth container class is missing from the login page."),
        )

    def test_signup_page_has_custom_styled_container(self):
        """
        Verifies that the signup page is rendered with our custom layout.
        """
        signup_url = reverse("account_signup")
        response = self.client.get(signup_url)

        self.assertEqual(
            response.status_code, 200, "Signup page did not return a 200 OK."
        )

        # Check for the presence of our custom auth-container class
        self.assertContains(
            response,
            'class="auth-container"',
            count=1,
            status_code=200,
            msg_prefix=("Auth container class is missing from the signup page."),
        )

    def test_password_reset_page_has_custom_styled_container(self):
        """
        Verifies that the password reset page is rendered with our custom layout.
        """
        password_reset_url = reverse("account_reset_password")
        response = self.client.get(password_reset_url)

        self.assertEqual(
            response.status_code, 200, "Password reset page did not return a 200 OK."
        )

        # Check for the presence of our custom auth-container class
        self.assertContains(
            response,
            'class="auth-container"',
            count=1,
            status_code=200,
            msg_prefix=(
                "Auth container class is missing from the password reset page."
            ),
        )
