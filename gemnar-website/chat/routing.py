from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(
        r"ws/conversation/(?P<conversation_id>\w+)/$",
        consumers.ConversationConsumer.as_asgi(),
    ),
    re_path(
        r"ws/user/notifications/$",
        consumers.UserNotificationConsumer.as_asgi(),
    ),
    re_path(
        r"ws/admin/logs/$",
        consumers.AdminLogsConsumer.as_asgi(),
    ),
    re_path(
        r"ws/tweet-queue/(?P<organization_pk>\w+)/(?P<brand_pk>\w+)/$",
        consumers.TweetQueueConsumer.as_asgi(),
    ),
]
