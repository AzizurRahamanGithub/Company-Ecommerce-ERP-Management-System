from django.urls import path
from .views import (
    NotificationCreateAPIView,
    NotificationAdminListAPIView,
    MyNotificationsAPIView,
    mark_read_view,
    mark_read_all_view,
    DeleteNotificationAPIView,
)

urlpatterns = [
    # Admin/staff
    path(
        "",
        NotificationCreateAPIView.as_view(),
        name="notifications-create",
    ),
    path(
        "list/",
        NotificationAdminListAPIView.as_view(),
        name="notifications-admin-list",
    ),
    path("my/", MyNotificationsAPIView.as_view(), name="notifications-my"),
    path(
        "notifications/<int:pk>/read/", mark_read_view, name="notifications-mark-read"
    ),
    path("my/read-all/", mark_read_all_view, name="notifications-read-all"),
    path(
        "<int:pk>/delete/",
        DeleteNotificationAPIView.as_view(),
        name="notifications-delete",
    ),
]
