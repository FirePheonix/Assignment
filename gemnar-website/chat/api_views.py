from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatRoom, ChatConversation, Message
from .serializers import (
    ChatRoomSerializer,
    ChatRoomDetailSerializer,
    MessageSerializer,
    ChatConversationSerializer,
    ChatConversationDetailSerializer,
)
from website.models import User, Brand


class ConversationListView(generics.ListAPIView):
    """
    API view to list conversations for the current user
    Supports both legacy ChatRoom and new ChatConversation models
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return ChatConversationSerializer

    def get_queryset(self):
        user = self.request.user
        # Handle both DRF requests and regular Django requests
        if hasattr(self.request, "query_params"):
            chat_type = self.request.query_params.get("type", "all")
        else:
            chat_type = self.request.GET.get("type", "all")

        # Build the base query using OR conditions to avoid union issues
        if user.brands.exists():
            # User is a brand owner - include both participant and brand owner conversations
            base_query = (
                Q(participant1=user) | Q(participant2=user) | Q(brand__owner=user)
            )
        else:
            # Regular user - only participant conversations
            base_query = Q(participant1=user) | Q(participant2=user)

        # Apply the base query
        conversations = ChatConversation.objects.filter(base_query)

        # Filter by type
        if chat_type == "creators":
            # Only creator-to-creator conversations
            conversations = conversations.filter(brand__isnull=True)
        elif chat_type == "brands":
            # Only brand-related conversations
            conversations = conversations.filter(brand__isnull=False)

        return conversations.distinct().order_by("-updated_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Add user type info to response
        user_type = "brand" if request.user.brands.exists() else "creator"

        # Count conversations by type
        creator_chats = queryset.filter(brand__isnull=True).count()
        brand_chats = queryset.filter(brand__isnull=False).count()

        return Response(
            {
                "user_type": user_type,
                "chats": serializer.data,
                "creator_chats": creator_chats,
                "brand_chats": brand_chats,
                "total_chats": queryset.count(),
            }
        )


class ConversationDetailView(generics.RetrieveAPIView):
    """
    API view to get a specific conversation with messages
    """

    serializer_class = ChatConversationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Get conversations where user is a participant or brand owner
        queryset = ChatConversation.objects.filter(
            Q(participant1=user) | Q(participant2=user) | Q(brand__owner=user)
        )

        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Mark messages as read - only mark messages sent by the other party
        Message.objects.filter(conversation=instance).exclude(
            sender=request.user
        ).update(is_read=True)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ConversationMessageListCreateView(generics.ListCreateAPIView):
    """
    API view to list messages in a conversation and create new messages
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        conversation_id = self.kwargs.get("conversation_id")
        user = self.request.user

        # Get the conversation and verify access
        conversation = get_object_or_404(ChatConversation, id=conversation_id)

        # Check if user has access to this conversation
        if not (
            user == conversation.participant1
            or user == conversation.participant2
            or (conversation.brand and user == conversation.brand.owner)
        ):
            return Message.objects.none()

        return Message.objects.filter(conversation=conversation)

    def perform_create(self, serializer):
        conversation_id = self.kwargs.get("conversation_id")
        user = self.request.user

        # Get the conversation and verify access
        conversation = get_object_or_404(ChatConversation, id=conversation_id)

        # Check if user has access to this conversation
        if not (
            user == conversation.participant1
            or user == conversation.participant2
            or (conversation.brand and user == conversation.brand.owner)
        ):
            raise permissions.PermissionDenied(
                "You don't have permission to send messages in this conversation"
            )

        # Save the message
        message = serializer.save(sender=user, conversation=conversation)

        # Update the conversation's updated_at timestamp
        conversation.save(update_fields=["updated_at"])

        # Send WebSocket notification to all participants
        channel_layer = get_channel_layer()
        room_group_name = f"conversation_{conversation_id}"

        # Broadcast the message to all WebSocket connections in this conversation
        message_data = {
            "type": "chat_message",
            "message_id": message.id,
            "message": message.get_decrypted_content(),
            "user_id": user.id,
            "username": user.username,
            "timestamp": message.timestamp.isoformat(),
            # Include image_url so real-time clients can display attachments
            "image_url": (
                self.request.build_absolute_uri(message.image.url)
                if message.image and hasattr(message.image, "url")
                else None
            ),
        }
        print(
            "📡 API: Broadcasting to '%s': id=%s user=%s"
            % (room_group_name, message.id, user.id)
        )

        try:
            async_to_sync(channel_layer.group_send)(room_group_name, message_data)
            print("✅ API: Message broadcast successful")
        except Exception as e:
            print(f"❌ API: Message broadcast failed: {e}")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def start_conversation_with_user(request, user_id):
    """
    API endpoint to start a new conversation with another user
    This creates creator-to-creator conversations
    """
    current_user = request.user
    target_user = get_object_or_404(User, id=user_id)

    # Don't allow users to start conversations with themselves
    if current_user == target_user:
        return Response(
            {"error": "Cannot start conversation with yourself"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure consistent participant ordering to avoid duplicate conversations
    if current_user.id < target_user.id:
        participant1, participant2 = current_user, target_user
    else:
        participant1, participant2 = target_user, current_user

    # Check if conversation already exists (creator-to-creator)
    conversation, created = ChatConversation.objects.get_or_create(
        participant1=participant1,
        participant2=participant2,
        brand=None,  # This is a creator-to-creator conversation
    )

    # Send WebSocket notification if this is a new conversation
    if created:
        channel_layer = get_channel_layer()

        # Notify both participants about the new conversation
        for user in [participant1, participant2]:
            other_user = participant2 if user == participant1 else participant1
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "new_conversation",
                    "conversation_id": conversation.id,
                    "conversation_name": other_user.username,
                    "other_user": {
                        "id": other_user.id,
                        "username": other_user.username,
                        "full_name": other_user.get_full_name(),
                    },
                    "timestamp": conversation.created_at.isoformat(),
                },
            )

    serializer = ChatConversationDetailSerializer(
        conversation, context={"request": request}
    )

    return Response(
        {"conversation": serializer.data, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def start_conversation_with_brand(request, brand_id):
    """
    API endpoint to start a new conversation with a brand
    This creates creator-to-brand conversations
    """
    user = request.user
    brand = get_object_or_404(Brand, id=brand_id)

    # Don't allow brand owners to start conversations with their own brand
    if user == brand.owner:
        return Response(
            {"error": "Cannot start conversation with your own brand"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if conversation already exists
    conversation, created = ChatConversation.objects.get_or_create(
        participant1=brand.owner,
        participant2=user,
        brand=brand,
    )

    # Send WebSocket notification if this is a new conversation
    if created:
        channel_layer = get_channel_layer()

        # Notify both participants about the new conversation
        async_to_sync(channel_layer.group_send)(
            f"user_{brand.owner.id}",
            {
                "type": "new_conversation",
                "conversation_id": conversation.id,
                "conversation_name": user.username,
                "other_user": {
                    "id": user.id,
                    "username": user.username,
                    "full_name": user.get_full_name(),
                },
                "timestamp": conversation.created_at.isoformat(),
            },
        )

        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "new_conversation",
                "conversation_id": conversation.id,
                "conversation_name": brand.name,
                "other_user": {
                    "id": brand.owner.id,
                    "username": brand.owner.username,
                    "full_name": brand.owner.get_full_name(),
                },
                "timestamp": conversation.created_at.isoformat(),
            },
        )

    serializer = ChatConversationDetailSerializer(
        conversation, context={"request": request}
    )

    return Response(
        {"conversation": serializer.data, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def conversation_stats(request):
    """
    API endpoint to get conversation statistics for the current user
    """
    user = request.user

    # Get all conversations for the user using a single query to avoid union issues
    if user.brands.exists():
        # User is a brand owner - include both participant and brand owner conversations
        base_query = Q(participant1=user) | Q(participant2=user) | Q(brand__owner=user)
    else:
        # Regular user - only participant conversations
        base_query = Q(participant1=user) | Q(participant2=user)

    all_conversations = ChatConversation.objects.filter(base_query).distinct()

    # Count by type
    creator_chats = all_conversations.filter(brand__isnull=True).count()
    brand_chats = all_conversations.filter(brand__isnull=False).count()
    total_chats = all_conversations.count()

    # Count unread messages
    unread_messages = (
        Message.objects.filter(conversation__in=all_conversations, is_read=False)
        .exclude(sender=user)
        .count()
    )

    user_type = "brand" if user.brands.exists() else "creator"

    return Response(
        {
            "user_type": user_type,
            "total_chats": total_chats,
            "unread_messages": unread_messages,
            "creator_chats": creator_chats,
            "brand_chats": brand_chats,
        }
    )


# Legacy API views for backward compatibility
class ChatRoomListView(generics.ListAPIView):
    """
    Legacy API view - kept for backward compatibility
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Handle both DRF requests and regular Django requests
        if hasattr(self.request, "query_params"):
            chat_type = self.request.query_params.get("type", "all")
        else:
            chat_type = self.request.GET.get("type", "all")

        if user.brands.exists():
            # User is a brand owner
            brand_chats = ChatRoom.objects.filter(brand__owner=user)

            if chat_type == "creators":
                return brand_chats
            elif chat_type == "brands":
                return ChatRoom.objects.none()
            else:
                return brand_chats
        else:
            # Regular user (creator)
            creator_chats = ChatRoom.objects.filter(user=user)

            if chat_type == "creators":
                return ChatRoom.objects.none()
            elif chat_type == "brands":
                return creator_chats
            else:
                return creator_chats

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        user_type = "brand" if request.user.brands.exists() else "creator"

        return Response({"user_type": user_type, "chats": serializer.data})


class ChatRoomDetailView(generics.RetrieveAPIView):
    """
    Legacy API view - kept for backward compatibility
    """

    serializer_class = ChatRoomDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.brands.exists():
            return ChatRoom.objects.filter(brand__owner=user)
        else:
            return ChatRoom.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Message.objects.filter(room=instance).exclude(sender=request.user).update(
            is_read=True
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MessageListCreateView(generics.ListCreateAPIView):
    """
    Legacy API view - kept for backward compatibility
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        room_id = self.kwargs.get("room_id")
        user = self.request.user

        if user.brands.exists():
            chat_room = get_object_or_404(ChatRoom, id=room_id, brand__owner=user)
        else:
            chat_room = get_object_or_404(ChatRoom, id=room_id, user=user)

        return Message.objects.filter(room=chat_room)

    def perform_create(self, serializer):
        room_id = self.kwargs.get("room_id")
        user = self.request.user

        if user.brands.exists():
            chat_room = get_object_or_404(ChatRoom, id=room_id, brand__owner=user)
        else:
            chat_room = get_object_or_404(ChatRoom, id=room_id, user=user)

        serializer.save(sender=user, room=chat_room)
        chat_room.save(update_fields=["updated_at"])


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def start_chat_with_creator(request, creator_id):
    """
    Legacy API endpoint - kept for backward compatibility
    """
    user = request.user

    if not user.brands.exists():
        return Response(
            {"error": "Only brand owners can start chats with creators"},
            status=status.HTTP_403_FORBIDDEN,
        )

    creator = get_object_or_404(User, id=creator_id)
    brand = user.brands.first()

    if not brand:
        return Response(
            {"error": "No brand found for user"}, status=status.HTTP_400_BAD_REQUEST
        )

    chat_room, created = ChatRoom.objects.get_or_create(brand=brand, user=creator)

    serializer = ChatRoomDetailSerializer(chat_room, context={"request": request})

    return Response(
        {"chat_room": serializer.data, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def start_chat_with_brand(request, brand_id):
    """
    Legacy API endpoint - kept for backward compatibility
    """
    user = request.user

    if user.brands.exists():
        return Response(
            {"error": "Brand owners cannot start chats with other brands"},
            status=status.HTTP_403_FORBIDDEN,
        )

    brand = get_object_or_404(Brand, id=brand_id)

    chat_room, created = ChatRoom.objects.get_or_create(brand=brand, user=user)

    serializer = ChatRoomDetailSerializer(chat_room, context={"request": request})

    return Response(
        {"chat_room": serializer.data, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def chat_stats(request):
    """
    Legacy API endpoint - kept for backward compatibility
    """
    user = request.user

    if user.brands.exists():
        total_chats = ChatRoom.objects.filter(brand__owner=user).count()
        unread_messages = (
            Message.objects.filter(room__brand__owner=user, is_read=False)
            .exclude(sender=user)
            .count()
        )

        return Response(
            {
                "user_type": "brand",
                "total_chats": total_chats,
                "unread_messages": unread_messages,
                "creator_chats": total_chats,
                "brand_chats": 0,
            }
        )
    else:
        total_chats = ChatRoom.objects.filter(user=user).count()
        unread_messages = (
            Message.objects.filter(room__user=user, is_read=False)
            .exclude(sender=user)
            .count()
        )

        return Response(
            {
                "user_type": "creator",
                "total_chats": total_chats,
                "unread_messages": unread_messages,
                "creator_chats": 0,
                "brand_chats": total_chats,
            }
        )
