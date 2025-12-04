from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from organizations.models import Organization, OrganizationUser, OrganizationOwner
from website.models import Brand

User = get_user_model()


class BrandCreationTestCase(TestCase):
    """Test suite for organization brand creation and profile access"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create organization
        self.organization = Organization.objects.create(
            name="Test Organization", slug="test-org"
        )

        # Add user as admin to organization
        self.org_user = OrganizationUser.objects.create(
            user=self.user, organization=self.organization, is_admin=True
        )

        # Set organization owner
        OrganizationOwner.objects.create(
            organization=self.organization, organization_user=self.org_user
        )

        # URLs
        self.brand_create_url = reverse(
            "organization_brand_create",
            kwargs={"organization_pk": self.organization.pk},
        )

        # Login the user
        self.client.login(username="testuser", password="testpass123")

    def test_brand_creation_form_get(self):
        """Test that the brand creation form renders correctly"""
        response = self.client.get(self.brand_create_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Brand")
        self.assertContains(response, "Brand Name")
        self.assertContains(response, "Brand Website")
        self.assertContains(response, "Brand Description")
        self.assertContains(response, self.organization.name)

    def test_brand_creation_success(self):
        """Test successful brand creation"""
        brand_data = {
            "name": "Test Brand",
            "url": "https://testbrand.com",
            "description": "A test brand for testing purposes",
        }

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Check if brand was created
        self.assertTrue(Brand.objects.filter(name="Test Brand").exists())

        # Get created brand
        brand = Brand.objects.get(name="Test Brand")

        # Verify brand properties
        self.assertEqual(brand.name, "Test Brand")
        self.assertEqual(brand.url, "https://testbrand.com")
        self.assertEqual(brand.description, "A test brand for testing purposes")
        self.assertEqual(brand.owner, self.user)
        self.assertEqual(brand.organization, self.organization)
        self.assertIsNotNone(brand.slug)
        self.assertEqual(brand.slug, "test-brand")

        # Check redirect to brand detail
        expected_url = reverse(
            "organization_brand_detail",
            kwargs={"organization_pk": self.organization.pk, "brand_pk": brand.pk},
        )
        self.assertRedirects(response, expected_url)

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("created successfully" in str(m) for m in messages))

    def test_brand_creation_missing_fields(self):
        """Test brand creation with missing required fields"""
        # Test missing name
        brand_data = {"url": "https://testbrand.com", "description": "A test brand"}

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Should stay on form page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Brand name and URL are required")

        # Brand should not be created
        self.assertFalse(Brand.objects.filter(url="https://testbrand.com").exists())

    def test_brand_creation_invalid_url(self):
        """Test brand creation with invalid URL"""
        brand_data = {
            "name": "Test Brand",
            "url": "invalid-url",
            "description": "A test brand",
        }

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Should handle validation error
        self.assertEqual(response.status_code, 200)

        # Check if brand was created (Django should handle URL validation)
        # If it was created, check if it exists
        if Brand.objects.filter(name="Test Brand").exists():
            brand = Brand.objects.get(name="Test Brand")
            # URL field should handle this gracefully
            self.assertEqual(brand.url, "invalid-url")

    def test_brand_slug_generation(self):
        """Test that brand slug is generated correctly"""
        brand_data = {
            "name": "My Amazing Brand!",
            "url": "https://myamazingbrand.com",
            "description": "An amazing brand",
        }

        self.client.post(self.brand_create_url, data=brand_data)

        # Check if brand was created
        self.assertTrue(Brand.objects.filter(name="My Amazing Brand!").exists())

        brand = Brand.objects.get(name="My Amazing Brand!")
        self.assertEqual(brand.slug, "my-amazing-brand")

    def test_brand_profile_access(self):
        """Test that brand profile is accessible via slug"""
        # Create a brand first
        brand = Brand.objects.create(
            name="Test Brand",
            url="https://testbrand.com",
            description="A test brand",
            owner=self.user,
            organization=self.organization,
        )

        # Test brand profile URL
        profile_url = reverse("website:brand_profile", kwargs={"slug": brand.slug})
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Brand")
        self.assertContains(response, "Visit Website")
        self.assertContains(response, "testbrand.com")

    def test_brand_with_reserved_name(self):
        """Test brand creation with reserved name"""
        # Try to create a brand with a reserved name
        brand_data = {
            "name": "Admin",  # This should be in RESERVED_BRAND_NAMES
            "url": "https://admin.com",
            "description": "Admin brand",
        }

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Should show error message
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Error creating brand" in str(m) for m in messages))

    def test_brand_duplicate_slug_handling(self):
        """Test that duplicate slugs are handled correctly"""
        # Create first brand
        Brand.objects.create(
            name="Test Brand",
            url="https://testbrand1.com",
            owner=self.user,
            organization=self.organization,
        )

        # Try to create second brand with same name
        brand_data = {
            "name": "Test Brand",
            "url": "https://testbrand2.com",
            "description": "Another test brand",
        }

        self.client.post(self.brand_create_url, data=brand_data)

        # Should succeed with different slug
        self.assertEqual(Brand.objects.filter(name="Test Brand").count(), 2)

        # Check that slugs are different
        brands = Brand.objects.filter(name="Test Brand").order_by("id")
        self.assertEqual(brands[0].slug, "test-brand")
        self.assertEqual(brands[1].slug, "test-brand-1")

    def test_non_admin_cannot_create_brand(self):
        """Test that non-admin users cannot create brands"""
        # Create another user
        non_admin_user = User.objects.create_user(
            username="nonadmin", email="nonadmin@example.com", password="testpass123"
        )

        # Add as non-admin member
        OrganizationUser.objects.create(
            user=non_admin_user, organization=self.organization, is_admin=False
        )

        # Login as non-admin
        self.client.login(username="nonadmin", password="testpass123")

        # Try to access brand creation form
        response = self.client.get(self.brand_create_url)

        # Should be redirected
        self.assertEqual(response.status_code, 302)

        # Try to create brand via POST
        brand_data = {
            "name": "Test Brand",
            "url": "https://testbrand.com",
            "description": "A test brand",
        }

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Should be redirected, not create brand
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Brand.objects.filter(name="Test Brand").exists())

    def test_brand_creation_with_special_characters(self):
        """Test brand creation with special characters in name"""
        brand_data = {
            "name": "Brand & Co. (2024)",
            "url": "https://brandco.com",
            "description": "A brand with special characters",
        }

        self.client.post(self.brand_create_url, data=brand_data)

        # Should handle special characters
        self.assertTrue(Brand.objects.filter(name="Brand & Co. (2024)").exists())

        brand = Brand.objects.get(name="Brand & Co. (2024)")
        self.assertEqual(brand.slug, "brand-co-2024")

    def test_brand_creation_error_handling(self):
        """Test error handling in brand creation"""
        # Test with extremely long name
        brand_data = {
            "name": "X" * 300,  # Exceeds CharField max_length
            "url": "https://testbrand.com",
            "description": "A test brand",
        }

        response = self.client.post(self.brand_create_url, data=brand_data)

        # Should handle error gracefully
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Error creating brand" in str(m) for m in messages))

    def test_brand_absolute_url(self):
        """Test that brand.get_absolute_url() works correctly"""
        brand = Brand.objects.create(
            name="Test Brand",
            url="https://testbrand.com",
            owner=self.user,
            organization=self.organization,
        )

        expected_url = reverse("website:brand_profile", kwargs={"slug": brand.slug})
        self.assertEqual(brand.get_absolute_url(), expected_url)

    def test_brand_creation_flow_debug(self):
        """Debug test to trace the exact flow and identify issues"""
        print("\n=== DEBUGGING BRAND CREATION FLOW ===")

        # Step 1: Check initial state
        print(f"Organization: {self.organization.name} (pk={self.organization.pk})")
        print(f"User: {self.user.username} (is_admin={self.org_user.is_admin})")
        print(f"Brand count before: {Brand.objects.count()}")

        # Step 2: GET request to form
        response = self.client.get(self.brand_create_url)
        print(f"GET response status: {response.status_code}")
        print(f"GET response content length: {len(response.content)}")

        # Step 3: POST request to create brand
        brand_data = {
            "name": "Debug Test Brand",
            "url": "https://debugbrand.com",
            "description": "Debug test brand",
        }

        response = self.client.post(self.brand_create_url, data=brand_data, follow=True)
        print(f"POST response status: {response.status_code}")
        print(f"POST response content length: {len(response.content)}")

        # Step 4: Check if brand was created
        brand_count = Brand.objects.count()
        print(f"Brand count after: {brand_count}")

        if brand_count > 0:
            brand = Brand.objects.get(name="Debug Test Brand")
            print(f"Brand created: {brand.name} (slug={brand.slug})")
            print(f"Brand profile URL: {brand.get_absolute_url()}")

            # Test profile access
            profile_response = self.client.get(brand.get_absolute_url())
            print(f"Profile response status: {profile_response.status_code}")

        # Step 5: Check messages
        messages = list(get_messages(response.wsgi_request))
        print(f"Messages: {[str(m) for m in messages]}")

        # Step 6: Check final redirect
        print(f"Final URL: {response.request['PATH_INFO']}")

        print("=== END DEBUG ===\n")

        # Assert that everything worked
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Brand.objects.filter(name="Debug Test Brand").exists())
