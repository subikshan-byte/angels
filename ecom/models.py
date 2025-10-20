from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
# ---------------- CATEGORY ----------------
class Category(models.Model):
    c_id = models.AutoField(primary_key=True)
    c_name = models.CharField(max_length=100, default="")
    hot_choices=[
        ('none','none'),
        ('hot','hot'),
        ('trending','trending'),
        ('bestselling','bestsellin')
    ]
    hot=models.CharField(
    max_length=150,
    choices=hot_choices,
    default='none')
    slug = models.SlugField(unique=True, blank=True, null=True, default="")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.c_name) + f"-{self.c_id or '0'}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.c_name


# ---------------- PRODUCT ----------------

class Product(models.Model):
    p_id = models.AutoField(primary_key=True)
    p_name = models.CharField(max_length=1000, default="")
    small_title = models.CharField(max_length=1000, default="")
    small_desc = models.CharField(max_length=1000, default="")
    brand_name = models.CharField(max_length=1000, default="")
    desc = models.TextField(default="")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    del_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    save_upto=models.IntegerField(default=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)

    delivery_times=models.IntegerField(default=1)

    new_choice=[
        ("yes","yes"),
        ("no","no")
    ]
    new=models.CharField(
    max_length=150,
    choices=new_choice,
    default='jewelry')
    main_category = [
    ('jewelry','jewelry'),
    ('cosmetic', 'coesmetic'),
    ('skincare','skincare'),
]

    main_category_diff = models.CharField(
    max_length=1000,
    choices=main_category,
    default='non'
)
    STOCK_CHOICES = [
    ('in stock', 'In Stock'),
    ('out of stock', 'Out of Stock'),
]

    stock_status = models.CharField(
    max_length=150,
    choices=STOCK_CHOICES,
    default='in stock'
)
    WHERE = [
        ('bestselling', 'bestselling'),
        ('trending', 'trending'),
        ('first','first'),
        ('last','last')
    ]
    where= models.CharField(
        max_length=100,
        choices=WHERE,
        default='none'
    )

    WHERE_TO_DISPLAY_CHOICES = [
        ('home', 'Home'),
        ('none', 'None'),
    ]
    where_to_display = models.CharField(
        max_length=10,
        choices=WHERE_TO_DISPLAY_CHOICES,
        default='none'
    )
    slug = models.SlugField(unique=True, blank=True, null=True, default="")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.desc[:50]) + f"-{self.p_id or '0'}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.p_name


# ---------------- PRODUCT IMAGE ----------------
class ProductImage(models.Model):
    img_id = models.AutoField(primary_key=True)
    p_id = models.ForeignKey(Product, on_delete=models.CASCADE, default=1)
    image = models.ImageField(upload_to='images', blank=True, null=True, default="")
    slug = models.SlugField(unique=True, blank=True, null=True, default="")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"img-{self.img_id or '0'}-{slugify(self.p_id.desc[:20])}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.p_id}"


# ---------------- SIZE ----------------

class Size(models.Model):
    sid = models.AutoField(primary_key=True)
    size = models.CharField(max_length=10, default="")
    p_id = models.ForeignKey(Product, on_delete=models.CASCADE, default=1)
    slug = models.SlugField(unique=True, blank=True, null=True, default="")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.size)}-{self.sid or '0'}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.size
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.p_name}"

    def subtotal(self):
        return self.quantity * self.product.price
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.user.username
# ---------------- ORDER ----------------
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Payment'),
        ('cod', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.TextField(blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Razorpay payment ID
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='cod')
    def total_price(self):
        return sum(item.subtotal() for item in self.items.all())
    def __str__(self):
        return f"Order #{self.id} by {self.user.username} ({self.payment_method})"



# ---------------- ORDER ITEM ----------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price at purchase time

    def __str__(self):
        return f"{self.quantity} x {self.product.p_name} (Order #{self.order.id})"

    def subtotal(self):
        return self.quantity * self.price
from django.utils import timezone
import random

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        return (timezone.now() - self.created_at).seconds < 300  # 5 mins validity

    def __str__(self):
        return f"OTP for {self.user.username}"
from django.utils import timezone
import random

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percent = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.active and (not self.expiry_date or self.expiry_date > timezone.now())

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"


class OrderOTP(models.Model):
    user = models.OneToManyField(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.verified = False
        self.save()

    def is_valid(self):
        return (timezone.now() - self.created_at).seconds < 300  # 5 mins

    
    def __str__(self):
        if self.order:
            return f"OTP for Order #{self.order.id}"
        return f"OTP (no order linked)"
