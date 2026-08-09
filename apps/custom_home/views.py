
from apps.shop.models import Products
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.db.models import Sum, F, Value, Count, Q, DecimalField, IntegerField
from django.db.models.functions import Coalesce, TruncDate, Cast
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unfold.views import UnfoldModelAdminViewMixin
from django.contrib.auth import get_user_model
from apps.order.models import Order, OrderItem, PaymentHistory
from apps.notification.models import Notification

User = get_user_model()


class AdminDashboardView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = "dashboard.html"
    title = "Admin Dashboard"
    permission_required = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Access model_admin if needed
        model_admin = getattr(self.request, "model_admin", None)

        # Date ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # ---------- KPIs ----------
        total_orders = Order.objects.count()
        todays_orders = Order.objects.filter(ordered_date__date=today).count()

        # Pending deliveries (orders with pending status)
        pending_deliveries = Order.objects.filter(order_status="pending").count()

        total_users = User.objects.count()

        # Active users (users with orders in last 30 days)
        active_users = (
            User.objects.filter(order__ordered_date__gte=today - timedelta(days=30))
            .distinct()
            .count()
        )

        # Total revenue from completed payments
        total_revenue = (
            PaymentHistory.objects.filter(payment_status="completed")
            .aggregate(
                total=Coalesce(
                    Sum("amount"), Value(Decimal("0.00"), output_field=DecimalField())
                )
            )
            .get("total")
        ) or Decimal("0.00")

        # Total products sold
        total_products_sold = (
            OrderItem.objects.aggregate(
                total=Coalesce(Sum("quantity"), Value(0, output_field=IntegerField()))
            ).get("total")
            or 0
        )

        # Total unique products in catalog
        total_products = OrderItem.objects.values("product").distinct().count()

        # ---------- Daily Orders Chart (Last 7 Days) ----------
        daily_orders = (
            Order.objects.filter(ordered_date__date__gte=week_ago)
            .annotate(day=TruncDate("ordered_date"))
            .values("day")
            .annotate(
                total_orders=Count("id"),
                completed=Count("id", filter=Q(order_status="completed")),
                pending=Count("id", filter=Q(order_status="pending")),
            )
            .order_by("day")
        )

        # Fill in missing days
        date_dict = {
            today - timedelta(days=i): {"total_orders": 0, "completed": 0, "pending": 0}
            for i in range(6, -1, -1)
        }

        for record in daily_orders:
            date_dict[record["day"]] = {
                "total_orders": record["total_orders"],
                "completed": record["completed"],
                "pending": record["pending"],
            }

        daily_labels = [date.strftime("%a") for date in sorted(date_dict.keys())]
        daily_completed = [
            date_dict[date]["completed"] for date in sorted(date_dict.keys())
        ]
        daily_pending = [
            date_dict[date]["pending"] for date in sorted(date_dict.keys())
        ]

        # ---------- Order Status Pie Chart ----------
        order_status_breakdown = Order.objects.values("order_status").annotate(
            count=Count("id")
        )

        status_dict = {status[0]: 0 for status in Order.STATUS_CHOICES}
        for item in order_status_breakdown:
            status_dict[item["order_status"]] = item["count"]

        # Use actual status choices from model
        pie_labels = [status[1] for status in Order.STATUS_CHOICES]  # Display names
        pie_values = [status_dict[status[0]] for status in Order.STATUS_CHOICES]

        # ---------- Tables ----------
        recent_orders = Order.objects.select_related("user").order_by("-ordered_date")[
            :10
        ]

        payments_table = PaymentHistory.objects.select_related(
            "order", "order__user"
        ).order_by("-payment_date")[:10]

        # Notifications (paginated)
        notifications_qs = Notification.objects.all().order_by("-created_at")
        paginator = Paginator(notifications_qs, 10)
        page = self.request.GET.get("page", 1)
        notifications_page = paginator.get_page(page)

        # ---------- Charts ----------
        # Sales by Unit Type (since there's no category)
     # Sales by Category (CharField, তাই direct value)
        # Sales by Category (CharField, তাই direct value)
        sales_by_unit = (
            OrderItem.objects.values(category_name=F("product__category"))
            .annotate(
                total_sales=Coalesce(
                    Sum(
                        F("price") * F("quantity"),
                        output_field=DecimalField(max_digits=15, decimal_places=2),
                    ),
                    Value(Decimal("0.00"), output_field=DecimalField()),
                )
            )
            .order_by("-total_sales")
        )

        # Display name এর জন্য CATEGORY_CHOICES থেকে map করো
        category_display = dict(Products.CATEGORY_CHOICES)
        chart_labels = [category_display.get(row["category_name"], row["category_name"] or "Unknown") for row in sales_by_unit]
        chart_values = [float(row["total_sales"] or 0) for row in sales_by_unit]

        # Display name এর জন্য CATEGORY_CHOICES থেকে map করো
        category_display = dict(Products.CATEGORY_CHOICES)
        chart_labels = [category_display.get(row["category_name"], row["category_name"] or "Unknown") for row in sales_by_unit]
        chart_values = [float(row["total_sales"] or 0) for row in sales_by_unit]

        # Top 5 products by quantity
        top_products = (
            OrderItem.objects.values(name=F("product__name"))
            .annotate(
                total_qty=Coalesce(
                    Sum("quantity"), Value(0, output_field=IntegerField())
                )
            )
            .order_by("-total_qty")[:5]
        )
        top_labels = [row["name"] or "Unknown" for row in top_products]
        top_values = [int(row["total_qty"] or 0) for row in top_products]

        # Warning/Alert message
        # Check for pending orders older than 3 days
        old_pending = Order.objects.filter(
            order_status="pending", ordered_date__date__lt=today - timedelta(days=3)
        ).count()

        alert_message = None
        if old_pending > 0:
            alert_message = (
                f"⚠️ {old_pending} pending order(s) older than 3 days need attention!"
            )

        # ---------- Context ----------
        context.update(
            {
                # KPIs
                "total_orders": total_orders,
                "todays_orders": todays_orders,
                "pending_deliveries": pending_deliveries,
                "total_users": total_users,
                "active_users": active_users,
                "total_revenue": float(total_revenue),
                "total_products": total_products,
                "total_products_sold": total_products_sold,
                # Alert
                "alert_message": alert_message,
                # Daily Orders Chart
                "daily_labels": daily_labels,
                "daily_completed": daily_completed,
                "daily_pending": daily_pending,
                # Order Status Pie Chart
                "pie_labels": pie_labels,
                "pie_values": pie_values,
                # Tables
                "recent_orders": recent_orders,
                "payments_table": payments_table,
                "notifications_table": notifications_page,
                # Charts
                "chart_labels": chart_labels,
                "chart_values": chart_values,
                "top_labels": top_labels,
                "top_values": top_values,
            }
        )
        return context
