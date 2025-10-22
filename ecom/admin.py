from django.contrib import admin
from .models import Category, Product, ProductImage, Size, Cart, CartItem, UserProfile, Order, OrderItem,Coupon
admin.site.site_header = "Zapwaves Administration"
admin.site.site_title = "Zapwaves Admin Portal"
admin.site.index_title = "Welcome to Zapwaves Dashboard"
# ---------------- CATEGORY ----------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('c_id', 'c_name', 'hot', 'slug')      
    search_fields = ('c_name', 'slug')             
    list_filter = ('hot',)  # filter by hot/trending/bestselling
    prepopulated_fields = {'slug': ('c_name',)}

# ---------------- PRODUCT ----------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('p_id', 'p_name', 'desc', 'price', 'category', 'stock_status', 'slug')  
    list_filter = ('category', 'where_to_display', 'stock_status', 'main_category_diff') 
    search_fields = ('p_name', 'desc', 'slug', 'brand_name',"p_id")
    prepopulated_fields = {'slug': ('desc',)}
    autocomplete_fields = ['category']

# ---------------- PRODUCT IMAGE ----------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('img_id', 'p_id', 'slug')
    search_fields = ('p_id__p_id', 'p_id__p_name', 'slug')

    prepopulated_fields = {'slug': ('p_id',)}
    autocomplete_fields = ['p_id']

# ---------------- SIZE ----------------


# ---------------- CART ----------------
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total_price')
    search_fields = ('user__username',)
    list_filter = ('created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal')
    search_fields = ('product__p_name', 'cart__user__username')
    list_filter = ('cart', 'product')

# ---------------- USER PROFILE ----------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'mobile')
    search_fields = ('user__username', 'mobile')
    list_filter = ('user',)

# ---------------- ORDER ----------------
@admin.action(description="Mark selected orders as Shipped")
def mark_as_shipped(modeladmin, request, queryset):
    queryset.update(status='shipped')

@admin.action(description="Mark selected orders as Delivered")
def mark_as_delivered(modeladmin, request, queryset):
    queryset.update(status='delivered')

from django.contrib import admin
from .models import Order, OrderItem, UserProfile

# Inline admin for OrderItem
class OrderItemInline(admin.TabularInline):  # use admin.StackedInline if you want bigger form
    model = OrderItem
    extra = 0  # show only existing items by default
    fields = ('product', 'quantity', 'price', 'subtotal')
    readonly_fields = ('subtotal',)
from django.contrib import admin
from .models import Order, OrderItem, UserProfile


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_customer_name',
        'get_customer_email',
        'get_customer_mobile',
        'get_user_zipcode',
        'get_ordered_items',
        'total_price',
        'address',
        'payment_method',
        'status',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__userprofile__mobile',
        'id',
        'payment_method',
    )
    list_filter = ('status', 'created_at', 'payment_method')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    actions = ['mark_as_shipped', 'mark_as_delivered']

    # ✅ CUSTOMER NAME
    @admin.display(description="Customer Name")
    def get_customer_name(self, obj):
        return obj.user.first_name or obj.user.username or "-"

    # ✅ EMAIL
    @admin.display(description="Email")
    def get_customer_email(self, obj):
        return obj.user.email or "-"

    # ✅ MOBILE NUMBER
    @admin.display(description="Mobile No.")
    def get_customer_mobile(self, obj):
        try:
            return obj.user.userprofile.mobile or "-"
        except UserProfile.DoesNotExist:
            return "-"

    # ✅ ZIPCODE
    @admin.display(description="Zipcode")
    def get_user_zipcode(self, obj):
        try:
            return obj.user.userprofile.zip_code or "-"
        except UserProfile.DoesNotExist:
            return "-"

    # ✅ ORDERED ITEMS
    @admin.display(description="Ordered Items")
    def get_ordered_items(self, obj):
        return ", ".join([
            f"{item.product.p_name} ({item.quantity})"
            for item in obj.items.all()
        ]) or "-"

    # ✅ ACTIONS
    @admin.action(description="Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description="Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'active', 'expiry_date', 'is_valid_display')
    list_filter = ('active', 'expiry_date')
    search_fields = ('code',)
    ordering = ('-expiry_date',)

    def is_valid_display(self, obj):
        """Show whether the coupon is currently valid in the list display."""
        return obj.is_valid()
    is_valid_display.short_description = "Valid?"
    is_valid_display.boolean = True 
from .models import OfferImage

@admin.register(OfferImage)
class OfferImageAdmin(admin.ModelAdmin):
    list_display = ("img_id", "title", "active", "slug")
    list_filter = ("active",)
    search_fields = ("title", "slug")

