from django.db import models
from apps.auths.models import CustomUser 

class EmployeeManager(models.Manager):
    def create_employee(self, first_name, last_name, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        employee = self.model(first_name=first_name, last_name=last_name, email=email, **extra_fields)
        employee.set_password(password)
        employee.save(using=self._db)
        return employee

class EmployeeProfile(models.Model):
    # Status Choices
    STATUS_ACTIVE = 'Active'
    STATUS_VACATION = 'On vacation'
    STATUS_SICK = 'Of sick'
    STATUS_PARENTAL_LEAVE = 'Parental leave'
    STATUS_UNPAID_LEAVE = 'Unpaid Leave'
    STATUS_SUSPENDED = 'Suspended'
    STATUS_RETIRED = 'Retired'
    STATUS_FIRED = 'Fired'
    
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_VACATION, 'On vacation'),
        (STATUS_SICK, 'Of sick'),
        (STATUS_PARENTAL_LEAVE, 'Parental leave'),
        (STATUS_UNPAID_LEAVE, 'Unpaid Leave'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_RETIRED, 'Retired'),
        (STATUS_FIRED, 'Fired'),
    ]
    
    # Employment Type Choices
    TYPE_FULL_TIME = 'Full Time'
    TYPE_PART_TIME = 'Part Time'
    TYPE_INTERN = 'Intern'
    
    EMPLOYMENT_TYPE_CHOICES = [
        (TYPE_FULL_TIME, 'Full Time'),
        (TYPE_PART_TIME, 'Part Time'),
        (TYPE_INTERN, 'Intern'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='employee_profile')

    # Personal
    first_name = models.CharField(max_length=255, blank=True, null=True)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    extension = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    tin_number = models.CharField(max_length=20, blank=True, null=True)
    nis_number = models.CharField(max_length=20, blank=True, null=True)

    # Job
    job_category = models.CharField(max_length=255, blank=True, null=True)
    employment_type = models.CharField(
        max_length=50, 
        choices=EMPLOYMENT_TYPE_CHOICES, 
        blank=True, 
        null=True
    )
    start_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        default=STATUS_ACTIVE
    )
    note = models.TextField(blank=True, null=True)

    # Wage
    wage_period = models.CharField(max_length=50, blank=True, null=True)
    current_wage_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    allowance_name = models.CharField(max_length=255, blank=True, null=True)
    total_compensation = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    last_increase_date = models.DateField(blank=True, null=True)
    previous_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Module access flags
    can_view_admin = models.BooleanField(default=False)
    can_edit_admin = models.BooleanField(default=False)
    can_view_employee = models.BooleanField(default=False)
    can_edit_employee = models.BooleanField(default=False)
    can_view_customer = models.BooleanField(default=False)
    can_edit_customer = models.BooleanField(default=False)
    can_view_order = models.BooleanField(default=False)
    can_edit_order = models.BooleanField(default=False)
    can_view_sales = models.BooleanField(default=False)
    can_edit_sales = models.BooleanField(default=False)
    can_view_delivery = models.BooleanField(default=False)
    can_edit_delivery = models.BooleanField(default=False)
    can_view_delivery_mnt = models.BooleanField(default=False)
    can_edit_delivery_mnt = models.BooleanField(default=False)
    can_view_invoicing = models.BooleanField(default=False)
    can_edit_invoicing = models.BooleanField(default=False)
    can_view_milk_collection = models.BooleanField(default=False)
    can_edit_milk_collection = models.BooleanField(default=False)
    can_view_supplier_payment = models.BooleanField(default=False)
    can_edit_supplier_payment = models.BooleanField(default=False)
    can_view_production = models.BooleanField(default=False)
    can_edit_production = models.BooleanField(default=False)
    can_view_sanitation = models.BooleanField(default=False)
    can_edit_sanitation = models.BooleanField(default=False)
    can_view_notification = models.BooleanField(default=False)
    can_edit_notification = models.BooleanField(default=False)
    can_view_notification_mnt = models.BooleanField(default=False)
    can_edit_notification_mnt = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        indexes = [
            models.Index(fields=['user'], name='employee_user_idx'),
            models.Index(fields=['status'], name='employee_status_idx'),
            models.Index(fields=['employment_type'], name='employee_type_idx'),
        ]

    def __str__(self):
        return f"EmployeeProfile<{self.user.username}>"

    @property
    def is_active(self):
        """Get active status from related user model"""
        return self.user.is_active if self.user else False

    @is_active.setter
    def is_active(self, value):
        """Set active status to related user model"""
        if self.user:
            self.user.is_active = value
            self.user.save()