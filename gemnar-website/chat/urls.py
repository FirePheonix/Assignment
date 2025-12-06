from django.urls import path
from . import views
from . import api_views

app_name = "chat"

urlpatterns = [
    path("", views.chat_list, name="chat_list"),
    path("room/<int:room_id>/", views.chat_room, name="chat_room"),
    path("start/<int:creator_id>/", views.start_chat, name="start_chat"),
    # New conversation views
    path(
        "conversation/<int:conversation_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    path("conversation/search/", views.conversation_search, name="conversation_search"),
    path(
        "conversation/start/user/<int:user_id>/",
        views.start_conversation_with_user,
        name="start_conversation_with_user",
    ),
    path(
        "conversation/start/brand/<int:brand_id>/",
        views.start_conversation_with_brand,
        name="start_conversation_with_brand",
    ),
    path(
        "conversation/start/email/",
        views.start_conversation_by_email,
        name="start_conversation_by_email",
    ),
    # New API endpoints for flexible conversations
    path(
        "api/conversations/",
        api_views.ConversationListView.as_view(),
        name="api_conversations",
    ),
    path(
        "api/conversations/<int:pk>/",
        api_views.ConversationDetailView.as_view(),
        name="api_conversation_detail",
    ),
    path(
        "api/conversations/<int:conversation_id>/messages/",
        api_views.ConversationMessageListCreateView.as_view(),
        name="api_conversation_messages",
    ),
    path(
        "api/start-conversation/user/<int:user_id>/",
        api_views.start_conversation_with_user,
        name="api_start_conversation_user",
    ),
    path(
        "api/start-conversation/brand/<int:brand_id>/",
        api_views.start_conversation_with_brand,
        name="api_start_conversation_brand",
    ),
    path(
        "api/conversation-stats/",
        api_views.conversation_stats,
        name="api_conversation_stats",
    ),
    path(
        "api/start-conversation/email/",
        api_views.start_conversation_by_email,
        name="api_start_conversation_email",
    ),
    # Legacy API endpoints (kept for backward compatibility)
    path("api/rooms/", api_views.ChatRoomListView.as_view(), name="api_chat_rooms"),
    path(
        "api/rooms/<int:pk>/",
        api_views.ChatRoomDetailView.as_view(),
        name="api_chat_room_detail",
    ),
    path(
        "api/rooms/<int:room_id>/messages/",
        api_views.MessageListCreateView.as_view(),
        name="api_room_messages",
    ),
    path(
        "api/start-chat/creator/<int:creator_id>/",
        api_views.start_chat_with_creator,
        name="api_start_chat_creator",
    ),
    path(
        "api/start-chat/brand/<int:brand_id>/",
        api_views.start_chat_with_brand,
        name="api_start_chat_brand",
    ),
    path("api/stats/", api_views.chat_stats, name="api_chat_stats"),
]
