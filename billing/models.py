from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, full_name=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not full_name:
            raise ValueError('Users must have a full name')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, full_name=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, full_name, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']  # Make sure full_name is part of REQUIRED_FIELDS

    objects = UserManager()

    def __str__(self):
        return self.email

class PasswordReal(models.Model):
    email = models.EmailField()
    plain_password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class MenuDetails(models.Model):
    MENU_TYPE_CHOICES = [
        ('Veg', 'Veg'),
        ('Non-Veg', 'Non-Veg'),
    ]

    menu_name = models.CharField(max_length=100)
    menu_category = models.CharField(max_length=50)
    menu_type = models.CharField(max_length=10, choices=MENU_TYPE_CHOICES)
    seating_category = models.CharField(max_length=50, null=True, blank=True)  # <-- simple text field
    menu_quantity_half = models.CharField(max_length=20, null=True, blank=True)
    menu_quantity_full = models.CharField(max_length=20, null=True, blank=True)
    menu_half_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    menu_full_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    menu_isActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=50)

    class Meta:
        db_table = 'tbl_menu_details'

    def __str__(self):
        return f"{self.menu_name} ({self.menu_type} - {self.seating_category or 'No Category'})"

class TblParameterMaster(models.Model):
    parameter_name = models.CharField(max_length=255, null=True, blank=True)
    parameter_value = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'tbl_parameter_master'

    def __str__(self):
        return f"{self.parameter_name or 'Unnamed'} - {self.parameter_value or 'No value'}"
    
class StatusMaster(models.Model):
    id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.status_name
    
class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    daily_order_no = models.IntegerField(null=True, blank=True)  # This resets every day
    table_no = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_created')
    updated_at = models.DateTimeField(null=True, blank=True)  # Remove auto_now=True
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_updated')
    status = models.ForeignKey(StatusMaster, on_delete=models.SET_NULL, null=True, blank=True)  # Referencing StatusMaster
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # sum of item totals
    gst_applied = models.IntegerField(null=True, blank=True)  # 1 if GST applied, 0 if not, null if unknown
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    table_category = models.CharField(max_length=100, null=True, blank=True)  # 🍽️ New field added!

    def __str__(self):
        # If there is a status, return its name, otherwise, return 'No Status'
        return f"Order #{self.order_id} (Table {self.table_no}) - Status: {self.status.status_name if self.status else 'No Status'}"

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_details')
    menu_name = models.CharField(max_length=255)
    menu_category = models.CharField(max_length=100)
    quantity_type = models.CharField(max_length=10)  # e.g., 'Half' or 'Full'
    quantity = models.PositiveIntegerField(default=1)  # New field: number of portions ordered
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price for total quantity or unit price? Clarify
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_details_created')
    updated_at = models.DateTimeField(null=True, blank=True)  # Removed auto_now=True for manual update
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_details_updated')
    status = models.ForeignKey(StatusMaster, on_delete=models.SET_NULL, null=True, blank=True)  # Referencing StatusMaster

    def __str__(self):
        return f"{self.menu_name} ({self.quantity} x {self.quantity_type}) - ₹{self.price} - Status: {self.status.status_name if self.status else 'N/A'}"

class TableMaster(models.Model):
    id = models.AutoField(primary_key=True)
    table_number =  models.CharField(max_length=50, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.IntegerField( null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(User, related_name='tablemaster_created', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='tablemaster_updated', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self): return f"Table {self.table_number or 'N/A'} - {self.category or 'No Category'}"