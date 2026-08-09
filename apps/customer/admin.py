from django.contrib import admin
from django.http import HttpResponse
from datetime import datetime
from unfold.admin import ModelAdmin
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from .models import (
    Customer,
    CustomerContact,
    DeliveryArea,
    DeliveryCustOff,
)


# ==========================
# EXCEL EXPORT ACTION
# ==========================
def export_customers_to_excel(modeladmin, request, queryset):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Customers"

    # Styles
    header_font = Font(bold=True)
    header_fill = PatternFill(
        start_color="DDDDDD", end_color="DDDDDD", fill_type="solid"
    )
    center_align = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    headers = [
        "Business Name",
        "Customer Code",
        "Assign Price",
        "Discount (%)",
        "Tax Rate (%)",
        "Delivery Area",
        "Status",
        "Can Order",
        "User Email",
        "Active",
        "Primary Contact",
        "Phone",
        "Billing Email",
        "Created At",
    ]

    ws.append(headers)

    # Header styling
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
        ws.column_dimensions[get_column_letter(col)].width = 22

    queryset = queryset.select_related("user").prefetch_related("contacts")

    for customer in queryset:
        primary_contact = customer.contacts.filter(role="primary").first()

        ws.append(
            [
                customer.business_name,
                customer.customer_code,
                customer.assign_price,
                float(customer.customer_discount),
                float(customer.tax_rate),
                customer.delivery_area or "",
                customer.status or "",
                customer.can_order or "",
                customer.user.email if customer.user else "",
                customer.is_active,
                (
                    f"{primary_contact.first_name} {primary_contact.middle_name or ''}".strip()
                    if primary_contact
                    else ""
                ),
                primary_contact.phone_number if primary_contact else "",
                primary_contact.billing_email if primary_contact else "",
                customer.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    wb.save(response)
    return response


export_customers_to_excel.short_description = "📥 Export selected customers to Excel"


# ==========================
# INLINES
# ==========================
class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 1
    show_change_link = True
    fields = (
        "role",
        "first_name",
        "middle_name",
        "phone_number",
        "billing_email",
        "billing_businnes_name",
        "billing_address",
    )


# ==========================
# CUSTOMER ADMIN
# ==========================
@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    inlines = [CustomerContactInline]

    list_display = (
        "business_name",
        "customer_code",
        "assign_price",
        "delivery_area",
        "status",
        "is_active",
        "created_at",
    )
    list_filter = ("assign_price", "status", "delivery_area")
    search_fields = (
        "business_name",
        "customer_code",
        "user__email",
        "user__username",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    actions = [export_customers_to_excel]

    class Media:
        css = {"all": ("admin/custom_actions.css",)}


# ==========================
# DELIVERY AREA ADMIN
# ==========================
@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "region", "created_at", "updated_at")
    list_filter = ("city", "region")
    search_fields = ("name", "city", "region")
    ordering = ("created_at",)


@admin.register(DeliveryCustOff)
class DeliveryCustOffAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "created_at", "updated_at")
    search_fields = ("name",)
    list_filter = ("date", "created_at")


# ==========================
# UNREGISTER CONTACT
# ==========================
try:
    admin.site.unregister(CustomerContact)
except admin.sites.NotRegistered:
    pass
