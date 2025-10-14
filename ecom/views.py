from django.http import HttpResponse
from django.shortcuts import redirect, render,get_object_or_404
from .models import Cart, CartItem, Product, ProductImage,Size
from datetime import datetime,timedelta
# Helper function to get product data including first image
def get_product_data(products):
    product_list = []
    for product in products:
        product_image = ProductImage.objects.filter(p_id=product).first()
        image_url = product_image.image.url if (product_image and product_image.image and hasattr(product_image.image, 'url')) else None
        product_dict = {
            'p_id': product.p_id,
            'p_name': product.p_name,
            'small_title': product.small_title,
            'small_desc': product.small_desc,
            'brand_name': product.brand_name,
            'desc': product.desc,
            'price': product.price,
            'del_price': product.del_price,
            'category': product.category.c_name,
            'delivery_times': product.delivery_times,
            'save': product.save_upto,                     # new column
            'new': product.new,                       # new column
            'main_category_diff': product.main_category_diff,
            'stock_status': product.stock_status,
            'where': product.where,
            'where_to_display': product.where_to_display,
            'slug': product.slug,
            'image_url': image_url
        }
        product_list.append(product_dict)
    return product_list



def home(request):
    # ------------------ FIRST PRODUCTS ------------------
    first_products = Product.objects.filter(where_to_display='home', where='first')
    first_product_data = get_product_data(first_products)
    first_product = first_product_data[0] if first_product_data else None
    other_first_products = first_product_data[1:] if len(first_product_data) > 1 else []

    # ------------------ TRENDING PRODUCTS ------------------
    trending_products = Product.objects.filter(where_to_display='home', where='trending')
    trending_product_data = get_product_data(trending_products)

    # ------------------ BESTSELLING PRODUCTS ------------------
    bestselling_products = Product.objects.filter(where_to_display='home', where='bestselling')
    bestselling_product_data = get_product_data(bestselling_products)

    # ------------------ LAST PRODUCTS ------------------
    last_products = Product.objects.filter(where_to_display='home', where='last')
    last_product_data = get_product_data(last_products)
    products = []
    price=0
    log='0'
    if not request.user.is_authenticated:
        log='1'
    else:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        
        for item in cart_items:
            product = item.product
            # attach quantity and subtotal
            price+=item.quantity*product.price
            product.quantity_in_cart = item.quantity
            product.subtotal_in_cart = item.subtotal()
            # attach first image url (or None if no image)
            first_image = product.productimage_set.first()
            product.image_url = first_image.image.url if first_image else ""
            products.append(product)
    # ------------------ CONTEXT ------------------
    context = {
        'first_product': first_product,
        'other_first_products': other_first_products,
        'trending_products': trending_product_data,
        'bestselling_products': bestselling_product_data,
        'last_products': last_product_data,
        "is_logged_in": request.user.is_authenticated,
        "user": request.user if request.user.is_authenticated else None,
        "cart":products,
        "price":price,
        "log":log
    }

    return render(request, 'home.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Product, ProductImage, Size

# Helper function to get product data including first image + sizes
def get_product_data1(products):
    product_list = []
    for product in products:
        product_image = ProductImage.objects.filter(p_id=product).first()
        image_url = product_image.image.url if (product_image and product_image.image and hasattr(product_image.image, 'url')) else None
        sizes = Size.objects.filter(p_id=product).values_list('size', flat=True)

        product_dict = {
            'p_id': product.p_id,
            'p_name': product.p_name,
            'small_title': product.small_title,
            'small_desc': product.small_desc,
            'brand_name': product.brand_name,
            'desc': product.desc,
            'price': product.price,
            'del_price': product.del_price,
            'category': product.category.c_name,
            'delivery_times': product.delivery_times,
            'save': product.save_upto,   # make sure field name matches your model
            'new': product.new,
            'main_category_diff': product.main_category_diff,
            'stock_status': product.stock_status,
            'where': product.where,
            'where_to_display': product.where_to_display,
            'slug': product.slug,
            'image_url':image_url
            'sizes': list(sizes)  # add sizes here
        }
        product_list.append(product_dict)
    return product_list
def product_detail(request, p):
    # ---------------- SPECIFIC PRODUCT ----------------
    product = get_object_or_404(Product, slug=p)

    # Main product (only one object, so wrap in list and unpack first)
    main_product_data = get_product_data1([product])[0]

    # All images of this product (not just the first one)

    # ---------------- SAME BRAND PRODUCTS ----------------
    same_brand_products = Product.objects.filter(
        brand_name=product.brand_name
    ).exclude(p_id=product.p_id)
    same_brand_data = get_product_data1(same_brand_products)

    # ---------------- SAME CATEGORY PRODUCTS ----------------
    same_category_products = Product.objects.filter(
        category=product.category
    ).exclude(p_id=product.p_id)
    same_category_data = get_product_data1(same_category_products)
    current_url=(request.build_absolute_uri()).replace("190.92.175.39:8000","angels-glamnglow.in")
    size=Size.objects.filter(p_id=product)
    # ---------------- CONTEXT ----------------
    products = []
    price=0
    log='0'
    if not request.user.is_authenticated:
        log='1'
    else:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        
        for item in cart_items:
            product = item.product
            # attach quantity and subtotal
            price+=item.quantity*product.price
            product.quantity_in_cart = item.quantity
            product.subtotal_in_cart = item.subtotal()
            # attach first image url (or None if no image)
            first_image = product.productimage_set.first()
            product.image_url = first_image.image.url if first_image else ""
            products.append(product)
    context = {
        'product': main_product_data,  
          'current_url': current_url,     # dict with all product details
             'size':size,     # queryset of all images
        'same_brand_products': same_brand_data,
        'same_category_products': same_category_data,
        "cart":products,
        "price":price,
        "log":log,
        "is_logged_in": request.user.is_authenticated,
        "user": request.user if request.user.is_authenticated else None,
    }

    return render(request, 'single-product.html', context)



def shop(request):
    return render(request,"single-product.html")
def product(request,p):
    return HttpResponse(p)
