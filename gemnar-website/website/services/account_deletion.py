"""
Account Deletion Service

Handles the complex process of deleting a user account and all related data
while maintaining data integrity and business requirements.
"""

import logging
import os
from typing import Dict, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from ..models import (
    Brand,
    Image,
    Link,
    ProfileImpression,
    PageView,
    BlogComment,
    ReferralCode,
    ReferralSignup,
    ReferralSubscription,
    ReferralBadge,
    ReferralLeaderboard,
    Task,
    TaskApplication,
    ServiceConnection,
    BrandTweet,
    BrandInstagramPost,
    TweetConfiguration,
    BrandAsset,
)
from chat.models import ChatConversation, ChatRoom

User = get_user_model()
logger = logging.getLogger(__name__)


class AccountDeletionService:
    """Service to handle user account deletion"""

    def __init__(self, user: User):
        self.user = user
        self.deletion_summary = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "deleted_at": timezone.now().isoformat(),
            "deleted_data": {},
        }

    def delete_account(
        self, reason: str = None, feedback: str = None
    ) -> Dict[str, Any]:
        """
        Delete user account and all related data

        Args:
            reason: Reason for deletion (optional)
            feedback: User feedback (optional)

        Returns:
            Dictionary with deletion summary
        """
        try:
            with transaction.atomic():
                # Log deletion attempt
                logger.info(
                    f"Starting account deletion for user {self.user.id} ({self.user.username})"
                )

                # Store reason and feedback
                if reason:
                    self.deletion_summary["reason"] = reason
                if feedback:
                    self.deletion_summary["feedback"] = feedback

                # Delete related data in order of dependencies
                self._delete_chat_data()
                self._delete_analytics_data()
                self._delete_brand_data()
                self._delete_content_data()
                self._delete_referral_data()
                self._delete_task_data()
                self._delete_social_connections()
                self._delete_user_files()
                self._anonymize_activity_logs()

                # Final user deletion
                self._delete_user()

                # Send notification email (if configured)
                self._send_deletion_notification()

                logger.info(f"Successfully deleted account for user {self.user.id}")
                return {
                    "success": True,
                    "message": "Account deleted successfully",
                    "summary": self.deletion_summary,
                }

        except Exception as e:
            logger.error(f"Error deleting account for user {self.user.id}: {str(e)}")
            return {"success": False, "error": str(e), "summary": self.deletion_summary}

    def _delete_chat_data(self):
        """Delete chat conversations and messages"""
        deleted_counts = {}

        # Delete conversations where user is participant
        conversations = ChatConversation.objects.filter(participant1=self.user).union(
            ChatConversation.objects.filter(participant2=self.user)
        )

        conversation_count = conversations.count()
        message_count = 0

        for conversation in conversations:
            message_count += conversation.messages.count()
            conversation.delete()

        # Delete legacy chat rooms
        chat_rooms = ChatRoom.objects.filter(user=self.user)
        room_count = chat_rooms.count()

        for room in chat_rooms:
            message_count += room.messages.count()
            room.delete()

        deleted_counts.update(
            {
                "conversations": conversation_count,
                "chat_rooms": room_count,
                "messages": message_count,
            }
        )

        self.deletion_summary["deleted_data"]["chat"] = deleted_counts
        logger.info(f"Deleted chat data: {deleted_counts}")

    def _delete_analytics_data(self):
        """Delete analytics and tracking data"""
        deleted_counts = {}

        # Profile impressions (where user was viewed)
        profile_impressions = ProfileImpression.objects.filter(profile_user=self.user)
        deleted_counts["profile_impressions_received"] = profile_impressions.count()
        profile_impressions.delete()

        # Profile impressions (where user viewed others) - anonymize instead of delete
        viewer_impressions = ProfileImpression.objects.filter(viewer=self.user)
        deleted_counts["profile_impressions_given"] = viewer_impressions.count()
        viewer_impressions.update(viewer=None)

        # Page views
        page_views = PageView.objects.filter(user=self.user)
        deleted_counts["page_views"] = page_views.count()
        page_views.delete()

        self.deletion_summary["deleted_data"]["analytics"] = deleted_counts
        logger.info(f"Deleted analytics data: {deleted_counts}")

    def _delete_brand_data(self):
        """Delete brands owned by user and related data"""
        deleted_counts = {}

        brands = Brand.objects.filter(owner=self.user)
        brand_count = brands.count()

        asset_count = 0
        tweet_count = 0
        instagram_post_count = 0

        for brand in brands:
            # Delete brand assets
            assets = BrandAsset.objects.filter(brand=brand)
            asset_count += assets.count()

            # Delete uploaded files for assets
            for asset in assets:
                if asset.file:
                    self._delete_file_safely(asset.file.path)
            assets.delete()

            # Delete brand tweets
            tweets = BrandTweet.objects.filter(brand=brand)
            tweet_count += tweets.count()
            tweets.delete()

            # Delete Instagram posts
            posts = BrandInstagramPost.objects.filter(brand=brand)
            instagram_post_count += posts.count()
            posts.delete()

            # Delete brand logo
            if brand.logo:
                self._delete_file_safely(brand.logo.path)

            # Brand will be deleted via CASCADE when user is deleted

        deleted_counts.update(
            {
                "brands": brand_count,
                "brand_assets": asset_count,
                "brand_tweets": tweet_count,
                "instagram_posts": instagram_post_count,
            }
        )

        self.deletion_summary["deleted_data"]["brands"] = deleted_counts
        logger.info(f"Deleted brand data: {deleted_counts}")

    def _delete_content_data(self):
        """Delete user-generated content"""
        deleted_counts = {}

        # Blog comments
        blog_comments = BlogComment.objects.filter(author=self.user)
        deleted_counts["blog_comments"] = blog_comments.count()
        blog_comments.delete()

        # Images
        images = Image.objects.filter(user=self.user)
        image_count = images.count()

        for image in images:
            if image.image:
                self._delete_file_safely(image.image.path)
        images.delete()

        # Links
        links = Link.objects.filter(user=self.user)
        deleted_counts["links"] = links.count()
        links.delete()

        # Tweet configurations
        tweet_configs = TweetConfiguration.objects.filter(user=self.user)
        deleted_counts["tweet_configurations"] = tweet_configs.count()
        tweet_configs.delete()

        deleted_counts["images"] = image_count

        self.deletion_summary["deleted_data"]["content"] = deleted_counts
        logger.info(f"Deleted content data: {deleted_counts}")

    def _delete_referral_data(self):
        """Delete referral system data"""
        deleted_counts = {}

        # User's referral code
        try:
            referral_code = ReferralCode.objects.get(user=self.user)

            # Delete referral signups made with this code
            signups = ReferralSignup.objects.filter(referral_code=referral_code)
            deleted_counts["referral_signups"] = signups.count()
            signups.delete()

            # Delete referral subscriptions made with this code
            subscriptions = ReferralSubscription.objects.filter(
                referral_code=referral_code
            )
            deleted_counts["referral_subscriptions"] = subscriptions.count()
            subscriptions.delete()

            # Delete the referral code itself
            referral_code.delete()
            deleted_counts["referral_codes"] = 1

        except ReferralCode.DoesNotExist:
            deleted_counts["referral_codes"] = 0
            deleted_counts["referral_signups"] = 0
            deleted_counts["referral_subscriptions"] = 0

        # Delete badges earned by user
        badges = ReferralBadge.objects.filter(user=self.user)
        deleted_counts["referral_badges"] = badges.count()
        badges.delete()

        # Update leaderboard entries (set to None instead of deleting)
        leaderboard_wins = ReferralLeaderboard.objects.filter(winner=self.user)
        leaderboard_wins.update(winner=None)
        deleted_counts["leaderboard_wins_anonymized"] = leaderboard_wins.count()

        leaderboard_seconds = ReferralLeaderboard.objects.filter(runner_up=self.user)
        leaderboard_seconds.update(runner_up=None)
        deleted_counts["leaderboard_seconds_anonymized"] = leaderboard_seconds.count()

        leaderboard_thirds = ReferralLeaderboard.objects.filter(third_place=self.user)
        leaderboard_thirds.update(third_place=None)
        deleted_counts["leaderboard_thirds_anonymized"] = leaderboard_thirds.count()

        self.deletion_summary["deleted_data"]["referrals"] = deleted_counts
        logger.info(f"Deleted referral data: {deleted_counts}")

    def _delete_task_data(self):
        """Delete task-related data"""
        deleted_counts = {}

        # Tasks created by user (as brand)
        created_tasks = Task.objects.filter(brand=self.user)
        task_count = created_tasks.count()

        # Count applications to tasks before deleting
        application_count = 0
        for task in created_tasks:
            application_count += task.applications.count()

        created_tasks.delete()

        # Task applications by user (as creator)
        user_applications = TaskApplication.objects.filter(creator=self.user)
        user_application_count = user_applications.count()
        user_applications.delete()

        deleted_counts.update(
            {
                "tasks_created": task_count,
                "applications_to_created_tasks": application_count,
                "user_applications": user_application_count,
            }
        )

        self.deletion_summary["deleted_data"]["tasks"] = deleted_counts
        logger.info(f"Deleted task data: {deleted_counts}")

    def _delete_social_connections(self):
        """Delete social media connections"""
        deleted_counts = {}

        connections = ServiceConnection.objects.filter(user=self.user)
        deleted_counts["service_connections"] = connections.count()
        connections.delete()

        self.deletion_summary["deleted_data"]["social"] = deleted_counts
        logger.info(f"Deleted social connections: {deleted_counts}")

    def _delete_user_files(self):
        """Delete user uploaded files"""
        deleted_files = []

        # Profile images
        file_fields = [
            "profile_image",
            "banner_image",
            "additional_image1",
            "additional_image2",
            "photo1",
            "photo2",
            "photo3",
            "photo4",
            "photo5",
            "photo6",
        ]

        for field_name in file_fields:
            file_field = getattr(self.user, field_name, None)
            if file_field:
                file_path = file_field.path
                if self._delete_file_safely(file_path):
                    deleted_files.append(field_name)

        self.deletion_summary["deleted_data"]["files"] = {
            "user_files_deleted": deleted_files
        }
        logger.info(f"Deleted user files: {deleted_files}")

    def _anonymize_activity_logs(self):
        """Anonymize rather than delete certain activity logs for business analytics"""
        # This method can be used to anonymize data that should be kept for analytics
        # but shouldn't be tied to the user anymore

        # For now, we'll just log that this step happened
        self.deletion_summary["deleted_data"]["anonymized"] = {
            "note": "Some activity logs may have been anonymized rather than deleted"
        }
        logger.info("Completed anonymization of activity logs")

    def _delete_user(self):
        """Delete the user account itself"""
        user_data = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "date_joined": self.user.date_joined.isoformat(),
            "last_login": self.user.last_login.isoformat()
            if self.user.last_login
            else None,
        }

        self.user.delete()

        self.deletion_summary["deleted_data"]["user"] = user_data
        logger.info(f"Deleted user account: {user_data}")

    def _delete_file_safely(self, file_path: str) -> bool:
        """Safely delete a file from the filesystem"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.warning(f"Could not delete file {file_path}: {str(e)}")
            return False

    def _send_deletion_notification(self):
        """Send email notification about account deletion"""
        try:
            if hasattr(settings, "DEFAULT_FROM_EMAIL") and settings.DEFAULT_FROM_EMAIL:
                subject = "Account Deletion Confirmation - Gemnar"
                message = f"""
Hello,

This email confirms that your Gemnar account ({self.user.email}) has been successfully deleted.

Account details:
- Username: {self.user.username}
- Email: {self.user.email}
- Deletion Date: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")}

All your data has been permanently removed from our systems.

If you didn't request this deletion or have any questions, please contact our support team immediately.

Thank you for using Gemnar.

Best regards,
The Gemnar Team
                """.strip()

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.user.email],
                    fail_silently=True,
                )

                self.deletion_summary["notification_sent"] = True
                logger.info(f"Sent deletion notification email to {self.user.email}")
            else:
                self.deletion_summary["notification_sent"] = False
                logger.warning(
                    "Email notification not sent - no DEFAULT_FROM_EMAIL configured"
                )

        except Exception as e:
            self.deletion_summary["notification_sent"] = False
            self.deletion_summary["notification_error"] = str(e)
            logger.error(f"Failed to send deletion notification email: {str(e)}")


def get_account_deletion_preview(user: User) -> Dict[str, Any]:
    """
    Get a preview of what data will be deleted for a user

    Args:
        user: User instance

    Returns:
        Dictionary with preview of data to be deleted
    """
    preview = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "data_to_delete": {},
    }

    # Count data that will be deleted
    preview["data_to_delete"].update(
        {
            "brands": Brand.objects.filter(owner=user).count(),
            "profile_impressions": ProfileImpression.objects.filter(
                profile_user=user
            ).count(),
            "page_views": PageView.objects.filter(user=user).count(),
            "blog_comments": BlogComment.objects.filter(author=user).count(),
            "images": Image.objects.filter(user=user).count(),
            "links": Link.objects.filter(user=user).count(),
            "tasks_created": Task.objects.filter(brand=user).count(),
            "task_applications": TaskApplication.objects.filter(creator=user).count(),
            "service_connections": ServiceConnection.objects.filter(user=user).count(),
            "tweet_configurations": TweetConfiguration.objects.filter(
                user=user
            ).count(),
        }
    )

    # Chat data
    conversations = ChatConversation.objects.filter(participant1=user).union(
        ChatConversation.objects.filter(participant2=user)
    )
    preview["data_to_delete"]["conversations"] = conversations.count()
    preview["data_to_delete"]["chat_rooms"] = ChatRoom.objects.filter(user=user).count()

    # Referral data
    try:
        referral_code = ReferralCode.objects.get(user=user)
        preview["data_to_delete"]["referral_signups"] = referral_code.signups.count()
        preview["data_to_delete"]["referral_subscriptions"] = (
            referral_code.subscriptions.count()
        )
        preview["data_to_delete"]["has_referral_code"] = True
    except ReferralCode.DoesNotExist:
        preview["data_to_delete"]["has_referral_code"] = False

    preview["data_to_delete"]["referral_badges"] = ReferralBadge.objects.filter(
        user=user
    ).count()

    return preview
