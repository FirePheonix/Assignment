from django.db.models import Q
from .models import Message


def unread_messages_count(request):
    """
    Context processor to add unread message count to all templates
    """
    if not request.user.is_authenticated:
        return {"unread_messages_count": 0}

    try:
        user = request.user

        # Count unread messages from conversations
        conversation_unread = (
            Message.objects.filter(conversation__isnull=False, is_read=False)
            .filter(
                Q(conversation__participant1=user)
                | Q(conversation__participant2=user)
                | Q(conversation__brand__owner=user)
            )
            .exclude(sender=user)
            .count()
        )

        # Count unread messages from legacy chat rooms
        room_unread = (
            Message.objects.filter(room__isnull=False, is_read=False)
            .filter(Q(room__user=user) | Q(room__brand__owner=user))
            .exclude(sender=user)
            .count()
        )

        total_unread = conversation_unread + room_unread

        return {"unread_messages_count": total_unread}
    except Exception:
        # In case of any error, return 0 to avoid breaking the template
        return {"unread_messages_count": 0}
