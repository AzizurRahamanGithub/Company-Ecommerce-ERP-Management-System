from django.db import models


class Products(models.Model):
    product_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    name = models.CharField(max_length=255)
    delivered_in_crate = models.CharField(
        max_length=255,
        choices=[("YES", "YES"), ("NO", "NO")],
    )
    products_per_crate = models.IntegerField(blank=True, null=True, default=1)
    crate_deposit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    images = models.JSONField(blank=True, null=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ========== NEW FIELDS ONLY ==========
    CATEGORY_CHOICES = [
        ("retail_milk_plain", "Retail Milk - Plain"),
        ("retail_milk_flv", "Retail Milk - Flv"),
        ("bulk_milk", "Bulk Milk"),
    ]
    
    AVAILABILITY_CHOICES = [
        ("in_stock", "In Stock"),
        ("out_of_stock", "Out of Stock"),
        ("coming_soon", "Coming Soon"),
        ("preorder", "Preorder"),
    ]
    
    PACKAGING_CHOICES = [
        ("container", "Container"),
        ("crate", "Crate"),
        ("box", "Box"),
    ]
    
    category = models.CharField(
        max_length=100, 
        choices=CATEGORY_CHOICES, 
        default="retail_milk_plain",
        blank=True,
        null=True
    )
    ar_account = models.CharField(
        max_length=100, 
        default="Retail Sales",
        blank=True,
        null=True
    )
    package_size = models.CharField(
        max_length=50, 
        default="1 kg",
        blank=True,
        null=True
    )
    factory_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    food_service_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    wholesale_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    distributor_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    partner_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True
    )
    availability = models.CharField(
        max_length=50,
        choices=AVAILABILITY_CHOICES,
        default="in_stock",
        blank=True,
        null=True
    )
    min_order_qty = models.CharField(
        max_length=50,
        default="1kg",
        blank=True,
        null=True
    )
    milk_used = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    cream_used = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    barcode = models.CharField(
        max_length=100,
    )
    packaging_items = models.CharField(
        max_length=100,
        choices=PACKAGING_CHOICES,
        default="container",
    )
    
    def calculate_combined_deposit(self):
        """Calculate combined deposit for crate/box"""
        if self.delivered_in_crate == "YES" and self.products_per_crate:
            return self.crate_deposit * self.products_per_crate
        return 0


    def __str__(self):
        return f"Products<{self.name}> ({self.delivered_in_crate}) - {self.original_price})"

