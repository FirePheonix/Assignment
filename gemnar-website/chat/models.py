from django.db import models
from django.conf import settings
from website.models import Brand


class ChatRoom(models.Model):
    """Legacy model for brand-creator chats - keeping for backward compatibility"""

    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["brand", "user"]

    def __str__(self):
        return f"Chat between {self.brand.name} and {self.user.username}"


class ChatConversation(models.Model):
    """
    Flexible chat model that supports:
    1. Creator-to-Creator chats (brand=None, participant1 and participant2 are users)
    2. Brand-to-Creator chats (brand set, participant1 is brand owner, participant2 is creator)
    """

    # For brand-creator chats
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, null=True, blank=True)

    # Participants (for creator-creator chats, both are regular users)
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_participant1",
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_as_participant2",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensure unique conversations between participants
        constraints = [
            models.UniqueConstraint(
                fields=["participant1", "participant2", "brand"],
                name="unique_conversation",
            ),
            models.CheckConstraint(
                check=~models.Q(participant1=models.F("participant2")),
                name="different_participants",
            ),
        ]

    def __str__(self):
        if self.brand:
            return f"Brand chat: {self.brand.name} ↔ {self.participant2.username}"
        else:
            return f"Creator chat: {self.participant1.username} ↔ {self.participant2.username}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.participant1:
            return self.participant2
        elif user == self.participant2:
            return self.participant1
        else:
            return None

    def is_brand_conversation(self):
        """Check if this is a brand-creator conversation"""
        return self.brand is not None

    def is_creator_conversation(self):
        """Check if this is a creator-creator conversation"""
        return self.brand is None


class Message(models.Model):
    # Keep existing room field for backward compatibility
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )

    # Add new conversation field for the flexible model
    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()  # Always encrypted
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to="chat_images/",
        null=True,
        blank=True,
        help_text="Optional image attachment for this message",
    )

    class Meta:
        ordering = ["timestamp"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(room__isnull=False, conversation__isnull=True)
                    | models.Q(room__isnull=True, conversation__isnull=False)
                ),
                name="message_belongs_to_room_or_conversation",
            )
        ]

    def save(self, *args, **kwargs):
        """Override save to automatically encrypt content."""
        if self.content:
            from .encryption import ChatEncryption

            try:
                # Try to decrypt first to see if it's already encrypted
                ChatEncryption.decrypt_message(self.content)
            except Exception:
                # If decryption fails, it's plain text, so encrypt it
                self.content = ChatEncryption.encrypt_message(self.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender.username}: {self.get_decrypted_content()[:50]}"

    def get_decrypted_content(self):
        """
        Get the decrypted content of the message using the master key.
        """
        try:
            from .encryption import ChatEncryption

            return ChatEncryption.decrypt_message(self.content)
        except Exception:
            # If decryption fails, assume it's plain text
            return self.content
