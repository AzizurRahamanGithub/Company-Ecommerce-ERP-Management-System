from django.contrib import admin
from django.http import HttpResponse
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from unfold.admin import ModelAdmin
from .models import (
    Order,
    OrderItem,
    PaymentHistory,
    DeliveryNote,
    Invoice,
    Review,
)


# -----------------------------
# OrderItem Inline for Admin
# -----------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "total_price")
    fields = ("product", "quantity", "price", "total_price")
    show_change_link = True
    can_delete = False


# -----------------------------
# PaymentHistory Inline for Admin
# -----------------------------
class PaymentHistoryInline(admin.TabularInline):
    model = PaymentHistory
    extra = 0
    readonly_fields = (
        "payment_method",
        "amount",
        "return_amount",
        "payment_status",
        "payment_date",
        "transaction_id",
    )
    fields = (
        "payment_method",
        "amount",
        "return_amount",
        "payment_status",
        "payment_date",
        "transaction_id",
    )
    show_change_link = True
    can_delete = False


# -----------------------------
# Admin for Order Model
# -----------------------------
@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "total_amount",
        "payment_method",
        "order_status",
        "ordered_date",
        "delivery_date",
        "delivery_area",
    )

    list_display_links = ("order_number",)

    list_filter = (
        "order_status",
        "payment_method",
        "ordered_date",
        "delivery_date",
        "delivery_area",
    )

    search_fields = (
        "order_number",
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "delivery_area",
    )

    inlines = [OrderItemInline, PaymentHistoryInline]

    list_per_page = 20

    date_hierarchy = "ordered_date"

    fieldsets = (
        (
            "Order Information",
            {
                "fields": (
                    ("order_number", "user"),
                    ("order_status", "payment_method"),
                    "total_amount",
                )
            },
        ),
        ("Dates", {"fields": (("ordered_date", "delivery_date"),)}),
        (
            "Customer & Delivery",
            {
                "fields": (
                    "customer_info",
                    "delivery_address",
                    "delivery_area",
                    "delivery_info",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "order_items",
                    "return_info",
                    "signature",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    readonly_fields = ("ordered_date",)
    ordering = ("-ordered_date",)

    # Unfold Admin settings
    list_filter_submit = True
    list_filter_always_visible = False

    # Custom actions
    actions = [
        "mark_as_pending",
        "mark_as_delivered",
        "mark_as_completed",
        "mark_as_cancelled",
        "export_as_excel",
    ]

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(order_status="pending")
        self.message_user(request, f"{updated} order(s) marked as Pending.")

    mark_as_pending.short_description = "Mark as Pending"

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(order_status="delivered")
        self.message_user(request, f"{updated} order(s) marked as Delivered.")

    mark_as_delivered.short_description = "Mark as Delivered"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(order_status="completed")
        self.message_user(request, f"{updated} order(s) marked as Completed.")

    mark_as_completed.short_description = "Mark as Completed"

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(order_status="cancelled")
        self.message_user(request, f"{updated} order(s) marked as Cancelled.")

    mark_as_cancelled.short_description = "Mark as Cancelled"

    def export_as_excel(self, request, queryset):
        """Export orders to Excel with detailed information"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Orders Export"

        # Styles
        header_fill = PatternFill(
            start_color="2563EB", end_color="2563EB", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True, size=11)
        header_alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )

        cell_border = Border(
            left=Side(style="thin", color="CCCCCC"),
            right=Side(style="thin", color="CCCCCC"),
            top=Side(style="thin", color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC"),
        )

        # Headers
        headers = [
            "Order Number",
            "Customer Name",
            "Customer Email",
            "Customer Phone",
            "Total Amount",
            "Payment Method",
            "Order Status",
            "Ordered Date",
            "Delivery Date",
            "Delivery Area",
            "Delivery Address",
            "Items Count",
            "Order Items Details",
        ]

        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = cell_border

        # Column widths
        column_widths = {
            "A": 15,
            "B": 20,
            "C": 25,
            "D": 15,
            "E": 12,
            "F": 15,
            "G": 15,
            "H": 18,
            "I": 15,
            "J": 20,
            "K": 40,
            "L": 12,
            "M": 60,
        }

        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # Write data
        for row_num, order in enumerate(
            queryset.select_related("user").prefetch_related("items"), 2
        ):
            # Extract customer info
            customer_info = order.customer_info or {}
            customer_name = (
                customer_info.get("name", "")
                or order.user.get_full_name()
                or order.user.username
            )
            customer_email = customer_info.get("email", "") or order.user.email
            customer_phone = customer_info.get("phone", "")

            # Extract delivery address
            delivery_address = order.delivery_address or {}
            if isinstance(delivery_address, dict):
                address_str = f"{delivery_address.get('street', '')}, {delivery_address.get('city', '')}, {delivery_address.get('state', '')} {delivery_address.get('zip', '')}"
            else:
                address_str = str(delivery_address)

            # Get order items details
            items = order.items.all()
            items_details = " | ".join(
                [
                    f"{item.product.name} (Qty: {item.quantity}, Price: ${item.price})"
                    for item in items
                ]
            )

            data = [
                order.order_number,
                customer_name,
                customer_email,
                customer_phone,
                float(order.total_amount),
                order.get_payment_method_display(),
                order.get_order_status_display(),
                order.ordered_date.strftime("%Y-%m-%d %H:%M:%S")
                if order.ordered_date
                else "",
                order.delivery_date.strftime("%Y-%m-%d") if order.delivery_date else "",
                order.delivery_area or "",
                address_str.strip(),
                items.count(),
                items_details,
            ]

            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = cell_border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

                # Alternate row colors
                if row_num % 2 == 0:
                    cell.fill = PatternFill(
                        start_color="F9FAFB", end_color="F9FAFB", fill_type="solid"
                    )

        # Freeze header
        ws.freeze_panes = "A2"

        # Response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        wb.save(response)

        self.message_user(
            request, f"{queryset.count()} order(s) exported to Excel successfully."
        )
        return response

    export_as_excel.short_description = "Export selected as Excel"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["inline_style"] = """
            <style>
                /* Action dropdown - Unfold specific styling */
                .unfold .select2-container--default .select2-selection--single {
                    background-color: #2563eb !important;
                    border-color: #2563eb !important;
                    height: 42px !important;
                    border-radius: 6px !important;
                }
                
                .unfold .select2-container--default .select2-selection--single .select2-selection__rendered {
                    color: white !important;
                    font-weight: 500 !important;
                    line-height: 40px !important;
                    padding-left: 12px !important;
                }
                
                .unfold .select2-container--default .select2-selection--single .select2-selection__arrow {
                    height: 40px !important;
                }
                
                .unfold .select2-container--default .select2-selection--single .select2-selection__arrow b {
                    border-color: white transparent transparent transparent !important;
                }
                
                /* Hover state */
                .unfold .select2-container--default .select2-selection--single:hover {
                    background-color: #1d4ed8 !important;
                    border-color: #1d4ed8 !important;
                }
                
                /* Focus state */
                .unfold .select2-container--default.select2-container--focus .select2-selection--single {
                    background-color: #1d4ed8 !important;
                    border-color: #1d4ed8 !important;
                    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3) !important;
                }
                
                /* Dropdown options */
                .unfold .select2-container--default .select2-results__option--highlighted[aria-selected] {
                    background-color: #2563eb !important;
                    color: white !important;
                }
                
                .unfold .select2-container--default .select2-results__option[aria-selected=true] {
                    background-color: #374151 !important;
                    color: white !important;
                }
                
                /* Dropdown container */
                .unfold .select2-container--default .select2-results__option {
                    padding: 8px 12px !important;
                }
                
                /* Make sure the dropdown itself looks good */
                .unfold .select2-dropdown {
                    border-color: #e5e7eb !important;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
                    border-radius: 6px !important;
                    margin-top: 4px !important;
                }
            </style>
        """
        return super().changelist_view(request, extra_context=extra_context)


# -----------------------------
# Admin for OrderItem Model
# -----------------------------
@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "price",
        "total_price",
    )

    list_display_links = ("order",)

    search_fields = (
        "order__order_number",
        "product__name",
    )

    list_filter = (
        "order__order_status",
        "product__category",
    )

    list_per_page = 25


# -----------------------------
# Admin for PaymentHistory Model
# -----------------------------
@admin.register(PaymentHistory)
class PaymentHistoryAdmin(ModelAdmin):
    list_display = (
        "order",
        "payment_method",
        "amount",
        "return_amount",
        "payment_status",
        "payment_date",
        "transaction_id",
    )

    list_display_links = ("order",)

    search_fields = (
        "order__order_number",
        "transaction_id",
    )

    list_filter = (
        "payment_status",
        "payment_method",
        "payment_date",
    )

    date_hierarchy = "payment_date"

    list_per_page = 25

    actions = ["export_as_excel"]

    def export_as_excel(self, request, queryset):
        """Export payment history to Excel"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Payment History"

        # Styles
        header_fill = PatternFill(
            start_color="16A34A", end_color="16A34A", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True, size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")

        cell_border = Border(
            left=Side(style="thin", color="CCCCCC"),
            right=Side(style="thin", color="CCCCCC"),
            top=Side(style="thin", color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC"),
        )

        # Headers
        headers = [
            "Order Number",
            "Payment Method",
            "Amount",
            "Return Amount",
            "Payment Status",
            "Transaction ID",
            "Payment Date",
        ]

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = cell_border

        # Column widths
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 12
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 25
        ws.column_dimensions["G"].width = 20

        # Write data
        for row_num, payment in enumerate(queryset.select_related("order"), 2):
            data = [
                payment.order.order_number if payment.order else "N/A",
                payment.get_payment_method_display(),
                float(payment.amount),
                float(payment.return_amount),
                payment.payment_status.upper(),
                payment.transaction_id or "",
                payment.payment_date.strftime("%Y-%m-%d %H:%M:%S"),
            ]

            for col_num, value in enumerate(data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = cell_border
                cell.alignment = Alignment(vertical="center")

                if row_num % 2 == 0:
                    cell.fill = PatternFill(
                        start_color="F9FAFB", end_color="F9FAFB", fill_type="solid"
                    )

        ws.freeze_panes = "A2"

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"payment_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        wb.save(response)

        self.message_user(
            request, f"{queryset.count()} payment(s) exported successfully."
        )
        return response

    export_as_excel.short_description = "Export as Excel"


# -----------------------------
# Admin for DeliveryNote Model
# -----------------------------
@admin.register(DeliveryNote)
class DeliveryNoteAdmin(ModelAdmin):
    list_display = ("order", "created_at")
    search_fields = ("order__order_number",)
    list_filter = ("created_at",)


# -----------------------------
# Admin for Invoice Model
# -----------------------------
@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = (
        "invoice_number",
        "order",
        "invoice_type",
        "payment_status",
        "invoice_date",
    )

    list_display_links = ("invoice_number",)

    search_fields = ("invoice_number", "order__order_number")
    list_filter = ("payment_status", "invoice_type", "invoice_date")

    date_hierarchy = "invoice_date"


# -----------------------------
# Admin for Review Model
# -----------------------------
@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = (
        "order_id",
        "user",
        "rating",
        "comment_preview",
        "created_at",
    )

    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "order_id__order_number", "comment")

    date_hierarchy = "created_at"

    list_per_page = 25

    def comment_preview(self, obj):
        if len(obj.comment) > 50:
            return obj.comment[:50] + "..."
        return obj.comment

    comment_preview.short_description = "Comment"
