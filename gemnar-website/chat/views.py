from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import ChatRoom, Message, ChatConversation
from website.models import User, Brand
import json


@login_required
def chat_list(request):
    """Show list of conversations for the current user (updated for new model)"""
    user = request.user

    # Get conversations using the new ChatConversation model
    if user.brands.exists():
        # User is a brand owner - include both participant and brand owner
        # conversations
        conversations = ChatConversation.objects.filter(
            Q(participant1=user) | Q(participant2=user) | Q(brand__owner=user)
        )
    else:
        # Regular user - only participant conversations
        conversations = ChatConversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        )

    conversations = conversations.distinct().order_by("-updated_at")

    # Get legacy chat rooms for backward compatibility
    if user.brands.exists():
        legacy_rooms = ChatRoom.objects.filter(brand__owner=user)
    else:
        legacy_rooms = ChatRoom.objects.filter(user=user)

    context = {
        "conversations": conversations,
        "legacy_rooms": legacy_rooms,
        "user_type": "brand" if user.brands.exists() else "creator",
    }

    return render(request, "chat/chat_list.html", context)


@login_required
def chat_room(request, room_id):
    """Show chat room and messages (legacy support)"""
    chat_room = get_object_or_404(ChatRoom, id=room_id)

    # Check if user has access to this room
    if not (request.user == chat_room.user or request.user == chat_room.brand.owner):
        return redirect("chat:chat_list")

    # Mark messages as read - only mark messages sent by the other party
    Message.objects.filter(room=chat_room).exclude(sender=request.user).update(
        is_read=True
    )

    chat_messages = chat_room.messages.all()

    return render(
        request,
        "chat/chat_room.html",
        {"chat_room": chat_room, "chat_messages": chat_messages},
    )


@login_required
def conversation_detail(request, conversation_id):
    """Show conversation detail with WebSocket support"""
    conversation = get_object_or_404(ChatConversation, id=conversation_id)

    # Check if user has access to this conversation
    user = request.user
    if not (
        user == conversation.participant1
        or user == conversation.participant2
        or (conversation.brand and user == conversation.brand.owner)
    ):
        return redirect("chat:chat_list")

    # Mark messages as read - only mark messages sent by the other party
    Message.objects.filter(conversation=conversation).exclude(sender=user).update(
        is_read=True
    )

    # Get chat messages for this conversation
    chat_messages = conversation.messages.all()

    # Get the other participant
    if conversation.brand:
        # Brand conversation
        other_participant = (
            conversation.participant2
            if user == conversation.brand.owner
            else conversation.brand.owner
        )
        conversation_title = f"{conversation.brand.name} Chat"
    else:
        # User-to-user conversation
        other_participant = conversation.get_other_participant(user)
        conversation_title = f"Chat with {other_participant.username}"

    context = {
        "conversation": conversation,
        "chat_messages": chat_messages,
        "other_participant": other_participant,
        "conversation_title": conversation_title,
        "is_brand_conversation": conversation.brand is not None,
    }

    return render(request, "chat/conversation_detail.html", context)


@login_required
def start_chat(request, creator_id):
    """Start a new chat with a creator (legacy support)"""
    # Get the creator
    creator = get_object_or_404(User, id=creator_id)

    # Check if the user is a brand owner
    if not request.user.brands.exists():
        return redirect("website:creator_profile", creator_id=creator_id)

    # Get the brand
    brand = request.user.brands.first()
    if not brand:
        return redirect("website:creator_profile", creator_id=creator_id)

    # Check if chat room already exists
    chat_room = ChatRoom.objects.filter(brand=brand, user=creator).first()

    if not chat_room:
        chat_room = ChatRoom.objects.create(brand=brand, user=creator)

    return redirect("chat:chat_room", room_id=chat_room.id)


@login_required
def start_conversation_with_user(request, user_id):
    """Start a new conversation with another user"""
    current_user = request.user
    target_user = get_object_or_404(User, id=user_id)

    # Don't allow users to start conversations with themselves
    if current_user == target_user:
        # Don't show Django message - just redirect quietly
        return redirect("chat:chat_list")

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

    # Conversation created or found - no need for Django messages in chat
    # Users will see the conversation directly

    return redirect("chat:conversation_detail", conversation_id=conversation.id)


@login_required
def start_conversation_with_brand(request, brand_id):
    """Start a new conversation with a brand"""
    user = request.user
    brand = get_object_or_404(Brand, id=brand_id)

    # Don't allow brand owners to start conversations with their own brand
    if user == brand.owner:
        # Don't show Django message - just redirect quietly
        return redirect("chat:chat_list")

    # Check if conversation already exists
    conversation, created = ChatConversation.objects.get_or_create(
        participant1=brand.owner,
        participant2=user,
        brand=brand,
    )

    # Conversation created or found - no need for Django messages in chat
    # Users will see the conversation directly

    return redirect("chat:conversation_detail", conversation_id=conversation.id)


@login_required
@require_POST
def start_conversation_by_email(request):
    """Start a new conversation with someone by their email address"""
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()

        if not email:
            return JsonResponse(
                {"success": False, "error": "Email address is required"}
            )

        # Find user by email
        try:
            target_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "No user found with this email address"}
            )

        current_user = request.user

        # Don't allow users to start conversations with themselves
        if current_user == target_user:
            return JsonResponse(
                {
                    "success": False,
                    "error": "You cannot start a conversation with yourself",
                }
            )

        # Check if current user is a brand owner
        if current_user.brands.exists():
            # Brand owner starting conversation with a user
            brand = current_user.brands.first()

            # Check if conversation already exists
            conversation, created = ChatConversation.objects.get_or_create(
                participant1=current_user,
                participant2=target_user,
                brand=brand,
            )

            conversation_type = "brand"
        else:
            # Regular user starting conversation with another user
            # Ensure consistent participant ordering to avoid duplicate
            # conversations
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

            conversation_type = "creator"

        return JsonResponse(
            {
                "success": True,
                "conversation_id": conversation.id,
                "created": created,
                "other_user": {
                    "id": target_user.id,
                    "username": target_user.username,
                    "email": target_user.email,
                },
                "conversation_type": conversation_type,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def conversation_search(request):
    """Search for users by email to start conversations"""
    return render(request, "chat/conversation_search.html")
