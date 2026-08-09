import django_filters
from django.utils.dateparse import parse_datetime
from .models import Notification, NotificationRecipient
from django.db import models

class NotificationAdminFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    type = django_filters.CharFilter(field_name='notification_type', lookup_expr='iexact')
    target_users = django_filters.CharFilter(field_name='target_users', lookup_expr='iexact')
    announcement = django_filters.BooleanFilter(field_name='is_announcement')
    search = django_filters.CharFilter(method='f_search')
    since = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    until = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Notification
        fields = ['status', 'notification_type', 'target_users', 'is_announcement']

    def f_search(self, qs, name, value):
        return qs.filter(
            models.Q(notification_title__icontains=value) |
            models.Q(notification_message__icontains=value)
        )

class MyRecipientFilter(django_filters.FilterSet):
    unread = django_filters.BooleanFilter(method='f_unread')            # unread=1
    delivered = django_filters.BooleanFilter(method='f_delivered')      # delivered=1
    announcement = django_filters.BooleanFilter(method='f_announcement')
    status = django_filters.CharFilter(field_name='notification__status', lookup_expr='iexact')
    type = django_filters.CharFilter(field_name='notification__notification_type', lookup_expr='iexact')
    search = django_filters.CharFilter(method='f_search')
    since = django_filters.IsoDateTimeFilter(field_name='notification__created_at', lookup_expr='gte')
    until = django_filters.IsoDateTimeFilter(field_name='notification__created_at', lookup_expr='lte')

    order = django_filters.OrderingFilter(
        fields=(
            ('notification__created_at', 'created_at'),
            ('notification__sent_at', 'sent_at'),
        )
    )

    class Meta:
        model = NotificationRecipient
        fields = []

    def f_unread(self, qs, name, value):
        return qs.filter(read_at__isnull=bool(value))

    def f_delivered(self, qs, name, value):
        if value:
            return qs.exclude(delivered_at__isnull=True)
        return qs.filter(delivered_at__isnull=True)

    def f_announcement(self, qs, name, value):
        return qs.filter(notification__is_announcement=value)

    def f_search(self, qs, name, value):
        return qs.filter(
            models.Q(notification__notification_title__icontains=value) |
            models.Q(notification__notification_message__icontains=value)
        )
