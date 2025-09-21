from django.contrib import admin
from .models import Category, Product, ProductImage, Size
# ---------------- CATEGORY ----------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('c_id', 'c_name', 'slug')      # show these in list view
    search_fields = ('c_name', 'slug')             # add search box
    prepopulated_fields = {'slug': ('c_name',)}    # auto-fill slug from name


# ---------------- PRODUCT ----------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('p_id','p_name', 'desc', 'price', 'category', 'slug')  
    list_filter = ('category', 'where_to_display') # filter sidebar
    search_fields = ('desc', 'slug')
    prepopulated_fields = {'slug': ('desc',)}      # auto-fill slug from description
    autocomplete_fields = ['category']             # choose category by name, not id


# ---------------- PRODUCT IMAGE ----------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('img_id', 'p_id', 'slug')
    search_fields = ('slug',)
    prepopulated_fields = {'slug': ('p_id',)}   
    autocomplete_fields = ['p_id']    # auto-slug (optional)


# ---------------- SIZE ----------------
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('sid', 'size', 'p_id', 'slug')
    search_fields = ('slug',)
    prepopulated_fields = {'slug': ('size',)}      # auto-slug (optional)
