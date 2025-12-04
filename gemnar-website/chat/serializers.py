from rest_framework import serializers
from .models import ChatRoom, ChatConversation, Message
from website.models import User, Brand


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "profile_picture",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_profile_picture(self, obj):
        if hasattr(obj, "profile_image") and obj.profile_image:
            # Handle Cloudinary URLs stored directly
            if obj.profile_image.name and ('cloudinary.com' in obj.profile_image.name or obj.profile_image.name.startswith('https://')):
                return obj.profile_image.name
            
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None


class BrandSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ["id", "name", "logo", "description"]

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.logo.url)
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    content = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "content", "sender", "timestamp", "is_read", "image_url"]
        read_only_fields = ["id", "sender", "timestamp"]

    def get_content(self, obj):
        """Return decrypted content instead of encrypted content."""
        return obj.get_decrypted_content()

    def create(self, validated_data):
        """Handle message creation with proper content handling."""
        # Get content from the request data (not validated_data since it's a
        # SerializerMethodField)
        request = self.context.get("request")
        content = request.data.get("content", "") if request else ""
        image = None
        if request and request.FILES.get("image"):
            image = request.FILES["image"]

        # Create the message with the content
        message = Message.objects.create(content=content, image=image, **validated_data)
        return message

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, "url"):
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


# Legacy serializers for backward compatibility
class ChatRoomSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    brand = serializers.CharField(source="brand.name", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "user",
            "brand",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
        ]

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                "content": last_message.get_decrypted_content(),
                "sender": last_message.sender.username,
                "timestamp": last_message.timestamp,
            }
        return None

    def get_unread_count(self, obj):
        user = self.context.get("request").user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class ChatRoomDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    brand = serializers.CharField(source="brand.name", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "user",
            "brand",
            "created_at",
            "updated_at",
            "messages",
            "display_name",
        ]

    def get_display_name(self, obj):
        user = self.context.get("request").user

        if user == obj.user:
            return obj.brand.name
        else:
            return obj.user.username


# New serializers for the flexible chat model
class ChatConversationSerializer(serializers.ModelSerializer):
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    brand = serializers.CharField(source="brand.name", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            "id",
            "participant1",
            "participant2",
            "brand",
            "created_at",
            "updated_at",
            "last_message",
            "unread_count",
            "display_name",
        ]

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                "content": last_message.get_decrypted_content(),
                "sender": last_message.sender.username,
                "timestamp": last_message.timestamp,
            }
        return None

    def get_unread_count(self, obj):
        user = self.context.get("request").user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_display_name(self, obj):
        user = self.context.get("request").user

        if obj.brand:
            return obj.brand.name
        elif obj.participant1 == user:
            return obj.participant2.username
        else:
            return obj.participant1.username


class ChatConversationDetailSerializer(serializers.ModelSerializer):
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    brand = serializers.CharField(source="brand.name", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            "id",
            "participant1",
            "participant2",
            "brand",
            "created_at",
            "updated_at",
            "messages",
            "display_name",
        ]

    def get_display_name(self, obj):
        user = self.context.get("request").user

        if obj.brand:
            return obj.brand.name
        elif obj.participant1 == user:
            return obj.participant2.username
        else:
            return obj.participant1.username
