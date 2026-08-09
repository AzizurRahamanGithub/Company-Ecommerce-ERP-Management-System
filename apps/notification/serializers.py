# yourapp/serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Notification, NotificationRecipient

User = get_user_model()


class RecipientMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecipient
        fields = ["user", "delivered_at", "read_at"]


class NotificationSerializer(serializers.ModelSerializer):
    # Write-only list of user IDs to target
    select_users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, required=False
    )
    recipients = RecipientMiniSerializer(many=True, source="notificationrecipient_set", read_only=True)
    total_number_of_users = serializers.IntegerField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_title",
            "notification_message",
            "is_announcement",
            "media_file",
            "is_scheduled",
            "schedule_time",
            "status",
            "sent_at",
            "created_at",
            "updated_at",
            "select_users",
            "recipients",
            "total_number_of_users",
        ]

    def validate(self, attrs):
        is_scheduled  = attrs.get("is_scheduled", getattr(self.instance, "is_scheduled", False))
        schedule_time = attrs.get("schedule_time", getattr(self.instance, "schedule_time", None))
        if is_scheduled:
            if not schedule_time:
                raise serializers.ValidationError({"schedule_time": "Required when scheduling."})
            if schedule_time <= timezone.now():
                raise serializers.ValidationError({"schedule_time": "Must be in the future."})
        return attrs

    def _set_recipients(self, obj, users):
        existing = set(NotificationRecipient.objects.filter(notification=obj).values_list("user_id", flat=True))
        for u in users:
            if u.id in existing:
                continue
            NotificationRecipient.objects.create(notification=obj, user=u)

    def create(self, validated_data):
        users = validated_data.pop("select_users", [])
        obj = Notification.objects.create(**validated_data)
        if users:
            self._set_recipients(obj, users)
        # Auto-queue composed messages to allow "send_now" action
        if not obj.is_scheduled and obj.notification_type == Notification.Type.COMPOSED:
            obj.status = Notification.Status.QUEUED
            obj.save(update_fields=["status"])
        return obj

    def update(self, instance, validated_data):
        users = validated_data.pop("select_users", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if users is not None:
            # reset recipients and set new ones
            NotificationRecipient.objects.filter(notification=instance).delete()
            self._set_recipients(instance, users)
        return instance




class NotificationCreateSerializer(serializers.Serializer):
    target_users = serializers.ChoiceField(choices=Notification.TARGET_USERS.choices)
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True, source='notification_title')
    message = serializers.CharField(source='notification_message')
    is_announcement = serializers.BooleanField(required=False, default=False)
    media_file = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    is_scheduled = serializers.BooleanField(required=False, default=False)
    schedule_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        is_scheduled = attrs.get('is_scheduled', False)
        schedule_time = attrs.get('schedule_time')
        if is_scheduled:
            if not schedule_time:
                raise serializers.ValidationError("schedule_time is required when is_scheduled=true")
            if schedule_time <= timezone.now():
                raise serializers.ValidationError("schedule_time must be in the future")
        return attrs

class NotificationAdminListSerializer(serializers.ModelSerializer):
    total_recipients = serializers.IntegerField(source='total_number_of_users', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'target_users', 'notification_type', 'status',
            'notification_title', 'notification_message', 'is_announcement', 'media_file',
            'is_scheduled', 'schedule_time', 'sent_at', 'created_at', 'updated_at',
            'total_recipients'
        ]

class MyNotificationSerializer(serializers.ModelSerializer):
    # Flatten NotificationRecipient + Notification
    id = serializers.IntegerField(source='notification.id', read_only=True)
    title = serializers.CharField(source='notification.notification_title')
    message = serializers.CharField(source='notification.notification_message')
    type = serializers.CharField(source='notification.notification_type')
    status = serializers.CharField(source='notification.status')
    is_announcement = serializers.BooleanField(source='notification.is_announcement')
    media_file = serializers.URLField(source='notification.media_file', allow_null=True)
    sent_at = serializers.DateTimeField(source='notification.sent_at', allow_null=True)
    created_at = serializers.DateTimeField(source='notification.created_at')
    delivered_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField()

    class Meta:
        model = NotificationRecipient
        fields = [
            'id', 'title', 'message', 'is_read',  'type', 'status', 'is_announcement', 'media_file',
            'delivered_at', 'read_at', 'sent_at', 'created_at'
        ]
