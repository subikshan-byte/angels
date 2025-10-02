from django.contrib import admin
from .models import Category, Product, ProductImage, Size, Cart, CartItem, UserProfile, Order, OrderItem

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
    search_fields = ('p_name', 'desc', 'slug', 'brand_name')
    prepopulated_fields = {'slug': ('desc',)}
    autocomplete_fields = ['category']

# ---------------- PRODUCT IMAGE ----------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('img_id', 'p_id', 'slug')
    search_fields = ('slug',)
    prepopulated_fields = {'slug': ('p_id',)}
    autocomplete_fields = ['p_id']

# ---------------- SIZE ----------------
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('sid', 'size', 'p_id', 'slug')
    search_fields = ('size', 'slug')
    list_filter = ('p_id',)
    prepopulated_fields = {'slug': ('size',)}

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
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'total_price')
    search_fields = ('user__username', 'id')
    list_filter = ('status', 'created_at')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price', 'subtotal')
    search_fields = ('order__id', 'product__p_name')
    list_filter = ('order', 'product')
