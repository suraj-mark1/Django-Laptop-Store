from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class LaptopBrand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Laptop(models.Model):
    name = models.CharField(max_length=100,default='unamed')
    brand = models.ForeignKey(LaptopBrand, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ram = models.CharField(max_length=50, blank=True, null=True)
    processor = models.CharField(max_length=100, blank=True, null=True)
    display = models.CharField(max_length=100, blank=True, null=True)
    storage = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='laptops/', null=True, blank=True)
    description = models.TextField()
    gpu = models.CharField(max_length=100, blank=True, null=True)
    screen_hertz = models.IntegerField(blank=True, null=True)
    ai_chip = models.CharField(max_length=100, blank=True, null=True)
    os=models.CharField(max_length=100,default='Windows')
    sold = models.IntegerField(default=0)
    stock = models.IntegerField(default=10)

    extra_features = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.brand.name} - {self.model}"
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.laptop.model}"
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    ordered_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default="India")

    def __str__(self):
        return f"{self.full_name}, {self.city}"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username
KEYBOARD_CHOICES = [
    ('rgb', 'RGB'),
    ('litekey', 'LiteKey'),
]
class CustomBuildRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ram = models.CharField(max_length=50)
    cpu = models.CharField(max_length=50)
    gpu = models.CharField(max_length=50)
    display = models.CharField(max_length=50)
    monitor = models.CharField(max_length=50)
    keyboard = models.CharField(max_length=50)
    ssd = models.CharField(max_length=50)
    storage = models.CharField(max_length=50)

    # Admin response fields
    is_possible = models.BooleanField(null=True, blank=True)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_response = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Build by {self.user.username}"

class Payment(models.Model):
    DELIVERY_CHOICES = [
        ('cash', 'Cash'),
        ('online', 'Online'),
    ]

    CASH_METHOD_CHOICES = [
        ('pay_on_delivery', 'Pay on Delivery'),
        ('delivery_online', 'Delivery Online'),
    ]

    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Order Confirmed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField()
    method = models.CharField(max_length=20, default='Unknown')  # Online or Cash
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_CHOICES)
    laptop = models.ForeignKey('Laptop', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Cash-specific
    cash_option = models.CharField(max_length=20, choices=CASH_METHOD_CHOICES, blank=True, null=True)

    # Online-specific
    card_name = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)

    is_successful = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_confirmed_by_admin = models.BooleanField(default=False)
    paid_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)  # ✅ if you really want it
    # ✅ New field for order tracking:
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    def __str__(self):
        laptop_name = self.laptop.model if self.laptop else "No Laptop"
        return f"{laptop_name} - {self.user.username} - {self.get_order_status_display()}"
#review
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    laptop = models.ForeignKey('Laptop', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.laptop.model} ({self.rating}★)"
class CustomerSupport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    complaint = models.TextField()
    response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%d-%m-%Y')}"
    
class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return - {self.order.id} by {self.user.username}"
# bapp/models.py

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    laptop = models.ForeignKey(Laptop, on_delete=models.CASCADE)
    date_purchased = models.DateField(auto_now_add=True)
