from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


from .models import Notification, NotificationRecipient
from .serializers import (
    NotificationCreateSerializer,
    NotificationAdminListSerializer,
    MyNotificationSerializer,
)
from .permissions import IsStaffOrAdmin
from .filters import NotificationAdminFilter, MyRecipientFilter
from .services import create_and_submit_notification
from apps.core.getList import BaseListAPIView
# ---------- Admin: create & list ----------


class NotificationCreateAPIView(generics.GenericAPIView):
    # permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    serializer_class = NotificationCreateSerializer

    def post(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        notif = create_and_submit_notification(
            target_users=data["target_users"],
            title=data.get("notification_title"),
            message=data["notification_message"],
            is_announcement=data.get("is_announcement", False),
            media_file=data.get("media_file"),
            is_scheduled=data.get("is_scheduled", False),
            schedule_time=data.get("schedule_time"),
        )
        out = NotificationAdminListSerializer(notif).data
        return Response(
            {
                "success": True,
                "statusCode": 200,
                "message": "Notification created successfully",
                "data": out,
            },
            status=status.HTTP_200_OK,
        )


class NotificationAdminListAPIView(BaseListAPIView):
    # permission_classes = [permissions.IsAuthenticated, IsStaffOrAdmin]
    serializer_class = NotificationAdminListSerializer
    queryset = Notification.objects.all().order_by("-created_at")
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = NotificationAdminFilter
    ordering_fields = ["created_at", "sent_at"]
    
        
        

# ---------- End-user: my notifications ----------


class MyNotificationsAPIView(BaseListAPIView):
    """
    Returns NotificationRecipient rows for the current user with the Notification fields flattened.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyNotificationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MyRecipientFilter
    ordering_fields = ["created_at", "sent_at"]
    ordering = ["-notification__created_at"]

    def get_queryset(self):
        return (
            NotificationRecipient.objects.select_related("notification")
            .filter(user=self.request.user)
            .order_by("-notification__created_at")
        )


# ---------- End-user: mark read ----------


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_read_view(request, pk: int):
    """
    Mark the current user's recipient row as read for notification {pk}.
    """
    rec = get_object_or_404(
        NotificationRecipient, notification_id=pk, user=request.user
    )
    rec.mark_read()
    return Response({"id": pk, "read_at": rec.read_at}, status=200)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def mark_read_all_view(request):
    """
    Mark all unread notifications for the current user as read.
    Unread = is_read=False (or read_at is NULL).
    """
    now = timezone.now()

    # Select unread only
    qs = NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False,           # primary condition
    )

    # Bulk update: set both flags
    updated = qs.update(is_read=True, read_at=now)

    # Summary after update
    summary = NotificationRecipient.summary_for_user(request.user)

    return Response(
        {
            "success": True,
            "message": "All unread notifications marked as read",
            "updated": updated,
            "read_at": now,
            "summary": summary,  # {"read": X, "unread": 0, "total": X}
        },
        status=status.HTTP_200_OK,
    )

class DeleteNotificationAPIView(mixins.DestroyModelMixin, generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyNotificationSerializer
    lookup_field = "pk"
    queryset = Notification.objects.all()  # Required

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()  # fetch object
        self.perform_destroy(instance)
        return Response({
            "success": True,
            "statusCode": 200,
            "message": "Notification deleted successfully",
        })

    def perform_destroy(self, instance):
        instance.delete()