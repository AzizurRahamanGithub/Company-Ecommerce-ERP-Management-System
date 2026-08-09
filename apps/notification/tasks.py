
from celery import shared_task


from .models import Notification, NotificationRecipient

def _deliver_to_user(rec: NotificationRecipient) -> bool:
    """
    Your actual delivery integration point.
    Replace with push/websocket/email/SMS/FCM/etc. 
    For demo, we just mark delivered.
    Return True if delivery succeeded.
    """
    # TODO: integrate real transport(s) here.
    rec.mark_delivered()
    return True

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def dispatch_notification_task(self, notification_id: int):
    try:
        notification = Notification.objects.select_for_update(nowait=False).get(pk=notification_id)
    except Notification.DoesNotExist:
        return

    # Ensure we're in a valid state to send
    if notification.status not in (Notification.Status.QUEUED, Notification.Status.SENDING):
        return

    # Idempotent dispatch lock
    acquired = notification.acquire_dispatch_lock()
    if not acquired:
        # Another worker is processing or it has already been processed
        return

    success = False
    try:
        # Fan-out recipients (idempotent)
        qs = notification.recipients_queryset().values_list('id', flat=True)
        # Bulk ensure recipients exist
        recipients = [
            NotificationRecipient(notification_id=notification.id, user_id=uid)
            for uid in qs
        ]
        NotificationRecipient.objects.bulk_create(recipients, ignore_conflicts=True)

        # Deliver
        rec_iter = NotificationRecipient.objects.filter(notification=notification).select_related('user').iterator()
        ok_count = 0
        for rec in rec_iter:
            if _deliver_to_user(rec):
                ok_count += 1

        # Consider partial failures as success for now (customize as needed)
        success = ok_count > 0 or NotificationRecipient.objects.filter(notification=notification).exists()

    except Exception as exc:
        # Backoff retry; lock will remain "sending", but we release below with failed state
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            success = False
    finally:
        notification.release_dispatch_lock(success=success)
