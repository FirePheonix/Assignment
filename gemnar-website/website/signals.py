"""
Django signals for the website app
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ProfileImpression

User = get_user_model()


# Removed automatic referral code generation for new users
# Users will now generate referral codes on-demand from the homepage


@receiver(post_save, sender=User)
def handle_user_referral_tracking(sender, instance, created, **kwargs):
    """Handle referral tracking when a user is created"""
    if created:
        # This signal doesn't have access to the request object
        # So we'll rely on the view to call handle_referral_signup directly
        pass


@receiver(post_save, sender=ProfileImpression)
def update_impressions_count_on_create(sender, instance, created, **kwargs):
    """Update user's impressions count when a new impression is created"""
    if created:
        user = instance.profile_user
        user.impressions_count = ProfileImpression.objects.filter(
            profile_user=user
        ).count()
        user.save(update_fields=["impressions_count"])


@receiver(post_delete, sender=ProfileImpression)
def update_impressions_count_on_delete(sender, instance, **kwargs):
    """Update user's impressions count when an impression is deleted"""
    user = instance.profile_user
    user.impressions_count = ProfileImpression.objects.filter(profile_user=user).count()
    user.save(update_fields=["impressions_count"])
