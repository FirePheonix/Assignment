from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from organizations.models import Organization, OrganizationUser, OrganizationOwner

User = get_user_model()


class OrganizationTest(TestCase):
    """Test suite for organization functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_can_create_organization(self):
        """Test that a logged-in user can create an organization"""
        # Login the user
        self.client.login(username="testuser", password="testpass123")

        # Data for organization creation
        org_data = {
            "name": "Test Organization",
            "slug": "test-organization-create",
        }

        # Post to organization creation view
        response = self.client.post(
            reverse("organization_add"), data=org_data, follow=True
        )

        # Check that organization was created
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Organization.objects.filter(name="Test Organization").exists())

        # Get the created organization
        organization = Organization.objects.get(name="Test Organization")

        # Verify organization properties
        self.assertEqual(organization.name, "Test Organization")
        self.assertEqual(organization.slug, "test-organization")

        # Verify user is added as organization member
        self.assertTrue(organization.users.filter(id=self.user.id).exists())

        # Verify OrganizationUser was created
        org_user = OrganizationUser.objects.get(
            user=self.user, organization=organization
        )
        self.assertTrue(org_user.is_admin)

        # Verify OrganizationOwner was created
        self.assertTrue(
            OrganizationOwner.objects.filter(
                organization=organization, organization_user=org_user
            ).exists()
        )

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("created successfully" in str(message) for message in messages)
        )

    def test_organization_shows_up_in_list(self):
        """Test that created organization appears in organization list"""
        # Login the user
        self.client.login(username="testuser", password="testpass123")

        # Create organization
        org_data = {
            "name": "Listed Organization",
            "slug": "listed-organization-list",
        }

        self.client.post(reverse("organization_add"), data=org_data, follow=True)

        # Get organization list
        response = self.client.get(reverse("organization_list"))

        # Check that organization appears in the list
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Listed Organization")
        self.assertIn("organization_list", response.context)

        # Verify organization is in the context
        organizations = response.context["organization_list"]
        self.assertEqual(organizations.count(), 1)
        self.assertEqual(organizations.first().name, "Listed Organization")

    def test_organization_detail_view_works(self):
        """Test that organization detail view works after creation"""
        # Login the user
        self.client.login(username="testuser", password="testpass123")

        # Create organization
        org_data = {
            "name": "Detail Test Organization",
            "slug": "detail-test-organization-detail",
        }

        self.client.post(reverse("organization_add"), data=org_data, follow=True)

        # Get the created organization
        organization = Organization.objects.get(name="Detail Test Organization")

        # Test organization detail view
        response = self.client.get(
            reverse("organization_detail", kwargs={"organization_pk": organization.pk})
        )

        # Check that detail view works
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Test Organization")
        self.assertIn("organization", response.context)
        self.assertEqual(response.context["organization"], organization)

    def test_anonymous_user_cannot_create_organization(self):
        """Test that anonymous users cannot create organizations"""
        # Try to create organization without login
        org_data = {
            "name": "Anonymous Organization",
            "slug": "anonymous-organization",
        }

        response = self.client.post(reverse("organization_add"), data=org_data)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)

        # Organization should not be created
        self.assertFalse(
            Organization.objects.filter(name="Anonymous Organization").exists()
        )

    def test_organization_creation_form_validation(self):
        """Test that organization creation form validates required fields"""
        # Login the user
        self.client.login(username="testuser", password="testpass123")

        # Try to create organization with missing name
        org_data = {
            "slug": "no-name-organization",
        }

        response = self.client.post(reverse("organization_add"), data=org_data)

        # Form should have errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")

        # Organization should not be created
        self.assertFalse(
            Organization.objects.filter(slug="no-name-organization").exists()
        )

    def test_multiple_organizations_per_user(self):
        """Test that a user can create multiple organizations"""
        # Login the user
        self.client.login(username="testuser", password="testpass123")

        # Create first organization
        org_data1 = {
            "name": "First Organization",
            "slug": "first-organization-multi",
        }

        self.client.post(reverse("organization_add"), data=org_data1, follow=True)

        # Create second organization
        org_data2 = {
            "name": "Second Organization",
            "slug": "second-organization-multi",
        }

        self.client.post(reverse("organization_add"), data=org_data2, follow=True)

        # Check both organizations exist
        self.assertTrue(Organization.objects.filter(name="First Organization").exists())
        self.assertTrue(
            Organization.objects.filter(name="Second Organization").exists()
        )

        # Check organization list shows both
        response = self.client.get(reverse("organization_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Organization")
        self.assertContains(response, "Second Organization")

        # Verify count in context
        organizations = response.context["organization_list"]
        self.assertEqual(organizations.count(), 2)
