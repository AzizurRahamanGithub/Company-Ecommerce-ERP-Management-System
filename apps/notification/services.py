# yourapp/services.py
from django.utils import timezone
from django.db import transaction
from .models import Notification, NotificationRecipient
from .tasks import dispatch_notification_task

def _fanout_recipients(notification: Notification) -> int:
    """
    Create NotificationRecipient rows for all intended recipients.
    Idempotent: uses unique_together(notification, user).
    Returns number of recipients created (or ensured exist).
    """
    users = notification.recipients_queryset().values_list('id', flat=True)
    # bulk_create with ignore conflicts (Django 3.1+ supports ignore_conflicts)
    recipients = [
        NotificationRecipient(notification_id=notification.id, user_id=uid)
        for uid in users
    ]
    created = NotificationRecipient.objects.bulk_create(
        recipients, ignore_conflicts=True
    )
    return len(recipients)  # total targeted (created or already existed)

@transaction.atomic
def send_now(notification: Notification) -> None:
    """Immediate send path (is_scheduled=False)."""
    notification.status = Notification.Status.QUEUED
    notification.is_scheduled = False
    notification.notification_type = Notification.Type.COMPOSED
    notification.save(update_fields=["status", "is_scheduled", "notification_type", "updated_at"])

    # 🔥 Fanout recipients before dispatch
    from .services import _fanout_recipients
    _fanout_recipients(notification)

    # Trigger Celery now
    dispatch_notification_task.apply_async(args=[notification.id])

@transaction.atomic
def schedule(notification: Notification) -> None:
    """Schedule path using Celery ETA."""
    notification.clean_for_schedule()
    notification.mark_queued()
    notification.save(update_fields=["status", "is_scheduled", "notification_type", "updated_at"])

    # 🔥 Fanout recipients before scheduling
    from .services import _fanout_recipients
    _fanout_recipients(notification)

    dispatch_notification_task.apply_async(args=[notification.id], eta=notification.schedule_time)


# def create_and_submit_notification(
#     *,
#     target_users: str,
#     title: str | None,
#     message: str,
#     is_announcement: bool = False,
#     media_file: str | None = None,
#     is_scheduled: bool = False,
#     schedule_time=None,
# ) -> Notification:
#     """
#     High-level API used by views/DRF/admin to create and either send now or schedule.
#     """
#     notif = Notification.objects.create(
#         target_users=target_users,
#         notification_type=Notification.Type.SCHEDULED if is_scheduled else Notification.Type.COMPOSED,
#         notification_title=title,
#         notification_message=message,
#         is_announcement=is_announcement,
#         media_file=media_file,
#         is_scheduled=is_scheduled,
#         schedule_time=schedule_time,
#         status=Notification.Status.DRAFT,
#     )
#     if is_scheduled:
#         schedule(notif)
#     else:
#         send_now(notif)
#     return notif
def create_and_submit_notification(
    *,
    target_users: str,
    title: str | None,
    message: str,
    is_announcement: bool = False,
    media_file: str | None = None,
    is_scheduled: bool = False,
    schedule_time=None,
) -> Notification:
    """
    High-level API used by views/DRF/admin to create and either send now or schedule.
    """
    notif = Notification.objects.create(
        target_users=target_users,
        notification_type=Notification.Type.SCHEDULED if is_scheduled else Notification.Type.COMPOSED,
        notification_title=title,
        notification_message=message,
        is_announcement=is_announcement,
        media_file=media_file,
        is_scheduled=is_scheduled,
        schedule_time=schedule_time,
        status=Notification.Status.DRAFT,
    )

    # 🔥 Fanout recipients immediately (for both types)
    from .services import _fanout_recipients
    _fanout_recipients(notif)

    # --- If scheduled: use Celery ETA ---
    if is_scheduled:
        schedule(notif)
    else:
        # --- If not scheduled: send instantly without Celery ---
        notif.status = Notification.Status.SENT
        notif.sent_at = timezone.now()
        notif.save(update_fields=["status", "sent_at", "updated_at"])

        # Directly deliver to users now 🔥
        recipients = NotificationRecipient.objects.filter(notification=notif)
        for rec in recipients:
            rec.mark_delivered()

    return notif
