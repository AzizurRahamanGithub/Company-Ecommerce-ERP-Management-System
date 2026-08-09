# yourapp/models.py
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """One logical message (customer blast / staff announcement / etc.)."""

    class Type(models.TextChoices):
        COMPOSED = "composed", "Composed"  # send now
        SCHEDULED = "scheduled", "Scheduled"  # send later

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        QUEUED = "queued", "Queued"  # accepted for schedule
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        CANCELED = "canceled", "Canceled"
        FAILED = "failed", "Failed"

    class TARGET_USERS(models.TextChoices):
        ALL = "all", "All"
        ADMIN = "admin", "Admin"
        EMPLOYEE = "employee", "Employee"
        USER = "user", "User"
        SANITIZER = "sanitizer", "Sanitizer"

    # ----- Fields -----

    # Target audience
    target_users = models.CharField(
        max_length=20, choices=TARGET_USERS.choices, default=TARGET_USERS.ALL
    )

    # Core content
    notification_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.COMPOSED
    )
    notification_title = models.CharField(max_length=200, blank=True, null=True)
    notification_message = models.TextField()

    # Optional media & announcement flag
    is_announcement = models.BooleanField(default=False)
    media_file = models.URLField(blank=True, null=True)

    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_time = models.DateTimeField(blank=True, null=True)

    # Lifecycle
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Idempotency / locking
    dispatch_lock = models.BooleanField(default=False)

    # Target users (through model stores read/delivery states)
    recipients = models.ManyToManyField(
        User,
        through="NotificationRecipient",
        related_name="notifications",
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["is_scheduled", "schedule_time"]),
        ]

    def __str__(self):
        return f"{self.notification_title} [{self.status}]"

    # ----- State helpers -----
    def clean_for_schedule(self):
        if self.is_scheduled and (
            not self.schedule_time or self.schedule_time <= timezone.now()
        ):
            raise ValueError(
                "Valid future schedule_time is required when is_scheduled=True."
            )

    def mark_queued(self):
        self.status = self.Status.QUEUED
        self.is_scheduled = True
        self.notification_type = self.Type.SCHEDULED

    def mark_sent(self):
        self.status = self.Status.SENT
        self.sent_at = timezone.now()

    @transaction.atomic
    def acquire_dispatch_lock(self) -> bool:
        """Lock for idempotent send."""
        updated = (
            Notification.objects.select_for_update()
            .filter(
                pk=self.pk,
                dispatch_lock=False,
                status__in=[self.Status.QUEUED, self.Status.SENDING],
            )
            .update(dispatch_lock=True, status=self.Status.SENDING)
        )
        return bool(updated)

    @transaction.atomic
    def release_dispatch_lock(self, success: bool):
        if success:
            self.mark_sent()
        else:
            self.status = self.Status.FAILED
        self.dispatch_lock = False
        self.save(update_fields=["status", "sent_at", "dispatch_lock", "updated_at"])

    # Convenience counters
    @property
    def total_number_of_users(self) -> int:
        return self.notificationrecipient_set.count()

    def recipients_queryset(self):
        """
        Returns a queryset of users based on target_users field.
        Compatible with your Role model.
        """
        if self.target_users == self.TARGET_USERS.ALL:
            return User.objects.all()
        elif self.target_users == self.TARGET_USERS.ADMIN:
            return User.objects.filter(role="admin")
        elif self.target_users == self.TARGET_USERS.EMPLOYEE:
            return User.objects.filter(role="employee")
        elif self.target_users == self.TARGET_USERS.USER:
            return User.objects.filter(role="user")
        elif self.target_users == self.TARGET_USERS.SANITIZER:
            return User.objects.filter(role="sanitizer")
        else:
            return User.objects.none()

class NotificationRecipient(models.Model):
    """
    Per-user state: whether a user received/read a notification, with timestamps.
    """

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["notification", "read_at"]),
        ]

    def mark_delivered(self):
        if not self.delivered_at:
            self.delivered_at = timezone.now()
            self.save(update_fields=["delivered_at"])

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


    # ---- User-centric summaries ----
    @classmethod
    def summary_for_user(cls, user: User) -> dict:
        qs = cls.objects.filter(user=user)
        total = qs.count()
        unread = qs.filter(is_read=False).count()  # or read_at__isnull=True
        return {"read": total - unread, "unread": unread, "total": total}