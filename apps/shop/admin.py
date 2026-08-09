import uuid
from django.db import transaction
from django import forms
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from .models import Products
from apps.file_uploader.upload_utils import (
    upload_file_to_digital_ocean,
    delete_file_from_digital_ocean,
)
from decimal import Decimal
from unfold.admin import ModelAdmin
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime

from .forms import  MultipleImagesForm

    
    
class ProductsAdminForm(forms.ModelForm):
    # Min. Order Qty = (number) + (Each/Crate)
    min_order_qty_number = forms.IntegerField(required=False, min_value=1, label="Min. Order Qty (Number)")
    min_order_qty_unit = forms.ChoiceField(
        required=False,
        choices=[("each", "Each"), ("crate", "Crate")],
        label="Min. Order Qty (Unit)"
    )

    class Meta:
        model = Products
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Rename labels (admin only)
        if "ar_account" in self.fields:
            self.fields["ar_account"].label = "AR Account"
        
        if "product_id" in self.fields:
            self.fields["product_id"].label = "Product ID"
                
        if "package_size" in self.fields:
            self.fields["package_size"].label = "Package Size"    
                
        if "products_per_crate" in self.fields:
            self.fields["products_per_crate"].label = "Number of Products per Crate/Box"    

        if "barcode" in self.fields:
            self.fields["barcode"].label = "Barcode/SKU"

        if "packaging_items" in self.fields:
            self.fields["packaging_items"].label = "Product Container"

        if "delivered_in_crate" in self.fields:
            self.fields["delivered_in_crate"].label = "Delivered In Crate/Box (YES/NO)"

        if "milk_used" in self.fields:
            self.fields["milk_used"].label = "Milk Used (Litres)"

        if "cream_used" in self.fields:
            self.fields["cream_used"].label = "Cream Used (Litres)"

        # Price naming (admin only)
        if "original_price" in self.fields:
            self.fields["original_price"].label = "Price"

        if "price" in self.fields:
            self.fields["price"].label = "Sale Price"
            self.fields["price"].required = False  # ✅ allow empty in admin UI

        # ✅ Parse stored min_order_qty string -> split fields
        raw = (getattr(self.instance, "min_order_qty", "") or "").strip()
        parts = raw.split()
        if len(parts) >= 2 and parts[0].isdigit():
            self.fields["min_order_qty_number"].initial = int(parts[0])
            unit = parts[1].lower()
            if unit in ("each", "crate"):
                self.fields["min_order_qty_unit"].initial = unit

    # ✅ litres validation (numeric)
    def clean_milk_used(self):
        v = self.cleaned_data.get("milk_used")
        try:
            # Directly convert to Decimal instead of using strip() for trimming string
            val = Decimal(v) if v else Decimal(0)
        except Exception:
            raise ValidationError("Milk Used must be a valid number in litres (e.g., 1.5).")
        if val < 0:
            raise ValidationError("Milk Used cannot be negative.")
        return val

    def clean_cream_used(self):
        v = self.cleaned_data.get("cream_used")
        try:
            # Convert to Decimal as well for consistency
            val = Decimal(v) if v else Decimal(0)
        except Exception:
            raise ValidationError("Cream Used must be a valid number in litres (e.g., 0.25).")
        if val < 0:
            raise ValidationError("Cream Used cannot be negative.")
        return val

    def clean(self):
        cleaned = super().clean()

        # ✅ combine min order qty
        n = cleaned.get("min_order_qty_number")
        u = cleaned.get("min_order_qty_unit")
        if n and u:
            cleaned["min_order_qty"] = f"{n} {u}"

        # ✅ on-sale logic: if sale price empty -> set sale = price
        price = cleaned.get("original_price")
        sale = cleaned.get("price")
        if (sale in (None, "", 0)) and price is not None:
            cleaned["price"] = price

        return cleaned


@admin.register(Products)
class ProductAdmin(ModelAdmin):
    form = type(
        "ProductsFullAdminForm",
        (ProductsAdminForm, MultipleImagesForm),
        {
            "Meta": type("Meta", (MultipleImagesForm.Meta,), {"model": Products}),
            "media_folder": "uploads/products",  # folder customize here
        },
    )
    summernote_fields = ("description",)

    list_filter_submit = True
    list_filter_always_visible = False

    # ✅ Duplicate action
    actions = ["duplicate_products"]

    # List Display (keep yours)
    list_display = (
        "product_image",
        "name",
        "category",
        "product_id_display",          # ✅ show product_id instead of id
        "ac_account_display",
        "package_size_display",
        "price_display",
        "factory_price_display",
        "food_service_display",
        "wholesale_display",
        "distributor_display",
        "partner_display",
        "availability_badge",
        "milk_used",
        "cream_used",
        "barcode",
        "packaging_items",
        "min_order_qty_display",
        "action_buttons",
    )

    list_display_links = ("product_image", "name")

    list_filter = (
        "category",
        "availability",
        "delivered_in_crate",
        "packaging_items",
        "created_at",
    )

    search_fields = (
        "name",
        "barcode",
        "ar_account",
        "product_id",   # ✅
    )

    ordering = ("-created_at",)
    list_per_page = 10

    # ✅ Organise page per your spec
    fieldsets = (
        (
            "BASIC INFORMATION",
            {
                "fields": (
                    ("name", "product_id"),             # ✅ add Product ID
                    ("category", "ar_account"),
                    ("barcode", "package_size"),        # ✅ Barcode/SKU in Basic Info
                    ("packaging_items", "delivered_in_crate"),
                    ( "products_per_crate",),          # only if model has it
                ),
            },
        ),
        ("DESCRIPTION", {
    "fields": (
        "description",
        "upload_images",   # ✅ এখানে রাখো
    )
}),


        (
            "PRODUCT COMPOSITION",
            {
                "fields": (("milk_used", "cream_used"),),
            },
        ),
        ("STOCK", {
    "fields": (
        ("availability",),
        ("min_order_qty_number", "min_order_qty_unit"),
    )
}),

        (
            "PRICING",
            {
                "fields": (
                    ("original_price", "price"),  # Price / Sale Price labels from form
                    ("factory_price", "food_service_price"),
                    ("wholesale_price", "distributor_price"),
                    "partner_price",
                ),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )


    readonly_fields = ("created_at",)
    
    @admin.display(description="Min Order QTY")
    def min_order_qty_display(self, obj):
        return obj.min_order_qty or 'N/A'
    
    @admin.display(description="AC Account")
    def ac_account_display(self, obj):
        return obj.min_order_qty or 'N/A'
    
    @admin.display(description="Packaging Items")
    def packaging_items_display(self, obj):
        return obj.packaging_items or 'N/A'
    
    @admin.display(description="Cream Used")
    def cream_used_display(self, obj):
        return obj.cream_used or 'N/A'
    
    @admin.display(description="Milk Used")
    def milk_used_display(self, obj):
        return obj.milk_used or 'N/A'
    
    @admin.display(description="Package Size")
    def package_size_display(self, obj):
        return obj.package_size or 'N/A'
    
    @admin.display(description="Product ID")
    def product_id_display(self, obj):
        return obj.product_id or 'N/A'
    
    @admin.display(description="Image")
    def product_image(self, obj):
        images = obj.images or []  # JSONField list
        if not isinstance(images, list) or len(images) == 0:
            return "—"

        first = images[0]
        if not first:
            return "—"

        return mark_safe(
            f'<a href="{first}" target="_blank">'
            f'<img src="{first}" style="height:50px;width:50px;object-fit:cover;border-radius:8px;border:1px solid #e5e7eb;" />'
            f'</a>'
        )

    def price_display(self, obj):
        return format_html(
            '<span style="color: #16a34a; font-weight: 600;">${}</span>', obj.price
        )

    price_display.short_description = "Retail Price"
    price_display.admin_order_field = "price"

    def factory_price_display(self, obj):
        if obj.factory_price:
            return format_html("<span>${}</span>", obj.factory_price)
        return "-"

    factory_price_display.short_description = "Factory"

    def food_service_display(self, obj):
        if obj.food_service_price:
            return format_html("<span>${}</span>", obj.food_service_price)
        return "-"

    food_service_display.short_description = "Food Service"

    def wholesale_display(self, obj):
        if obj.wholesale_price:
            return format_html("<span>${}</span>", obj.wholesale_price)
        return "-"

    wholesale_display.short_description = "Wholesale"

    def distributor_display(self, obj):
        if obj.distributor_price:
            return format_html("<span>${}</span>", obj.distributor_price)
        return "-"

    distributor_display.short_description = "Distributor"

    def partner_display(self, obj):
        if obj.partner_price:
            return format_html("<span>${}</span>", obj.partner_price)
        return "-"

    partner_display.short_description = "Partner"

    def availability_badge(self, obj):
        if not obj.availability:
            return "-"
        colors = {
            "in_stock": "#16a34a",
            "out_of_stock": "#dc2626",
            "coming_soon": "#ca8a04",
        }
        labels = {
            "in_stock": "In Stock",
            "out_of_stock": "Out of Stock",
            "coming_soon": "Coming Soon",
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; '
            'font-size: 11px; font-weight: 500;">{}</span>',
            colors.get(obj.availability, "#6b7280"),
            labels.get(obj.availability, obj.availability),
        )

    availability_badge.short_description = "Availability"
    availability_badge.admin_order_field = "availability"

    def action_buttons(self, obj):
        return format_html(
            '<a href="/admin/shop/products/{}/change/" style="background: #2563eb; color: white; '
            "padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; "
            'display: inline-block; margin-right: 4px;">Edit</a>'
            '<a href="/admin/shop/products/{}/delete/" style="background: #dc2626; color: white; '
            "padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; "
            'display: inline-block;">Delete</a>',
            obj.pk,
            obj.pk,
        )

    action_buttons.short_description = "Action"

    # Custom actions
    actions = ["mark_in_stock", "mark_out_of_stock", "export_as_csv", "export_as_excel", "duplicate_products"]
    
    @transaction.atomic
    def duplicate_products(self, request, queryset):
        duplicated = 0
        m2m_fields = [f.name for f in self.model._meta.many_to_many]

        for obj in queryset:
            old_obj = obj

            obj.pk = None

            if getattr(old_obj, "name", None):
                obj.name = f"{old_obj.name} (Copy)"

            # 👇 unique barcode generate
            if hasattr(obj, "barcode"):
                obj.barcode = str(uuid.uuid4())[:12]

            # 👇 unique product_id generate
            if hasattr(obj, "product_id"):
                obj.product_id = str(uuid.uuid4())[:8].upper()

            if hasattr(obj, "created_at"):
                obj.created_at = None

            obj.save()
            duplicated += 1

            for field_name in m2m_fields:
                getattr(obj, field_name).set(getattr(old_obj, field_name).all())

        self.message_user(request, f"✅ {duplicated} product(s) duplicated successfully.")

    duplicate_products.short_description = "Duplicate selected products"

    def mark_in_stock(self, request, queryset):
        updated = queryset.update(availability="in_stock")
        self.message_user(request, f"{updated} product(s) marked as In Stock.")

    mark_in_stock.short_description = "Mark selected as In Stock"

    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(availability="out_of_stock")
        self.message_user(request, f"{updated} product(s) marked as Out of Stock.")

    mark_out_of_stock.short_description = "Mark selected as Out of Stock"

    def export_as_csv(self, request, queryset):
        import csv

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="products_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "ID",
                "Name",
                "Category",
                "AR Account",
                "Package Size",
                "Price",
                "Factory",
                "Food Service",
                "Wholesale",
                "Distributor",
                "Partner",
                "Availability",
                "Milk Used",
                "Cream Used",
                "Barcode",
                "Packaging Items",
                "Min Order QTY",
                "Description",
            ]
        )

        for p in queryset:
            writer.writerow(
                [
                    p.id,
                    p.name,
                    p.get_category_display() if p.category else "",
                    p.ar_account or "",
                    p.package_size or "",
                    p.price,
                    p.factory_price or "",
                    p.food_service_price or "",
                    p.wholesale_price or "",
                    p.distributor_price or "",
                    p.partner_price or "",
                    p.get_availability_display() if p.availability else "",
                    p.milk_used or "",
                    p.cream_used or "",
                    p.barcode or "",
                    p.get_packaging_items_display() if p.packaging_items else "",
                    p.min_order_qty or "",
                    p.description or "",
                ]
            )

        return response

    export_as_csv.short_description = "Export selected as CSV"

    def export_as_excel(self, request, queryset):
        """
        Excel export with beautiful formatting
        """
        # Create workbook and sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Products Export"

        # Define styles
        header_fill = PatternFill(
            start_color="2563EB", end_color="2563EB", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True, size=12)
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
            "ID",
            "Name",
            "Category",
            "Delivered In Crate/Box",
            "AR Account",
            "Package Size",
            "Original Price",
            "Retail Price",
            "Factory Price",
            "Food Service Price",
            "Wholesale Price",
            "Distributor Price",
            "Partner Price",
            "Availability",
            "Milk Used",
            "Cream Used",
            "Barcode",
            "Packaging Items",
            "Min Order QTY",
            "Image URL",
            "Description",
            "Created At",
        ]

        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = cell_border

        # Adjust column widths
        column_widths = {
            "A": 8,  # ID
            "B": 30,  # Name
            "C": 20,  # Category
            "D": 20,  # Unit Type
            "E": 15,  # AR Account
            "F": 15,  # Package Size
            "G": 12,  # Original Price
            "H": 12,  # Retail Price
            "I": 12,  # Factory Price
            "J": 15,  # Food Service Price
            "K": 15,  # Wholesale Price
            "L": 15,  # Distributor Price
            "M": 12,  # Partner Price
            "N": 15,  # Availability
            "O": 12,  # Milk Used
            "P": 12,  # Cream Used
            "Q": 20,  # Barcode
            "R": 15,  # Packaging Items
            "S": 15,  # Min Order QTY
            "T": 40,  # Image URL
            "U": 50,  # Description
            "V": 20,  # Created At
        }

        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # Write data
        for row_num, product in enumerate(queryset, 2):
            data = [
                product.id,
                product.name,
                product.get_category_display() if product.category else "",
                product.get_delivered_in_crate_display() if product.delivered_in_crate else "",
                product.ar_account or "",
                product.package_size or "",
                float(product.original_price) if product.original_price else "",
                float(product.price) if product.price else "",
                float(product.factory_price) if product.factory_price else "",
                float(product.food_service_price) if product.food_service_price else "",
                float(product.wholesale_price) if product.wholesale_price else "",
                float(product.distributor_price) if product.distributor_price else "",
                float(product.partner_price) if product.partner_price else "",
                product.get_availability_display() if product.availability else "",
                product.milk_used or "",
                product.cream_used or "",
                product.barcode or "",
                product.get_packaging_items_display()
                if product.packaging_items
                else "",
                product.min_order_qty or "",
                product.product_image or "",
                product.description or "",
                product.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if product.created_at
                else "",
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

        # Freeze the header row
        ws.freeze_panes = "A2"

        # Create response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        wb.save(response)

        self.message_user(
            request, f"{queryset.count()} product(s) exported to Excel successfully."
        )
        return response

    export_as_excel.short_description = "Export selected as Excel"

    class Media:
        css = {"all": ("admin/css/products_custom.css",)}
        js = ("admin/js/products_custom.js",)

