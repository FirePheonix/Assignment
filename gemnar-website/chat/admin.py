from django.contrib import admin
from .models import ChatRoom, ChatConversation, Message


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("brand", "user", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("brand__name", "user__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("room", "sender", "content_preview", "timestamp", "is_read")
    list_filter = ("timestamp", "is_read")
    search_fields = ("content", "sender__username", "room__brand__name")
    readonly_fields = ("timestamp",)

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    content_preview.short_description = "Content Preview"


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = (
        "conversation_type",
        "participant1",
        "participant2",
        "brand",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "participant1__username",
        "participant2__username",
        "brand__name",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-updated_at",)

    def conversation_type(self, obj):
        return "Brand Chat" if obj.brand else "Creator Chat"

    conversation_type.short_description = "Type"

    fieldsets = (
        (
            "Conversation Information",
            {"fields": ("participant1", "participant2", "brand")},
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("participant1", "participant2", "brand")
        )
