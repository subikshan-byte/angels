from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from razorpay import Order
from .models import Cart, CartItem
from .models import Product,UserProfile
from .models import Order
from .models import OrderItem

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import OrderItem, ProductImage
from django.db.models import Prefetch
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect("login")   # only logged-in users can have cart
    product = get_object_or_404(Product, slug=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # get quantity from POST
    quantity = int(request.POST.get("quantity", 1))

    # Check if product already in cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        # Update quantity if already exists
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()

    return redirect("product", p=product.slug)


def account_detail(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    user = request.user
    profile = UserProfile.objects.get(user=request.user)

    # get all cart items for this user
    cart_items = CartItem.objects.filter(cart=cart)


    ordered_items = (
            OrderItem.objects
            .filter(order__user=user)
            .select_related("product", "order")
            .prefetch_related("product__productimage_set")  # fetch related images
        )
        # build context dictionary for template
    cart1 = []
    for item in ordered_items:
            # get first image if exists
            product_images = item.product.productimage_set.all()
            image_url = product_images[0].image.url if product_images else ""

            cart1.append({
                "slug":item.product.slug,
                "p_name": item.product.p_name,
                "image_url": image_url,
                "price": float(item.price*item.quantity),  # price at purchase time
                "qty": item.quantity,
                "status": item.order.status,

            })
    # get only products
    products = []
    for item in cart_items:
        product = item.product
        # dynamically add quantity and subtotal to product object
        product.quantity_in_cart = item.quantity
        product.subtotal_in_cart = item.subtotal()
        products.append(product)
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
    return render(request, "myaccount.html", {"cart1": cart1,"profile":profile,"is_logged_in": request.user.is_authenticated,
        "user": request.user if request.user.is_authenticated else None,"cart":products,
        "price":price,
        "log":log,})
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Save User table fields
        user.first_name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.save()

        # Save Profile table fields
        profile.mobile = request.POST.get("mobile")
        profile.address = request.POST.get("address")
        profile.save()
        return redirect("myaccount")
  # redirect after save


    return redirect("login")
def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        return redirect("login")

    cart_item = get_object_or_404(CartItem, product_id=item_id, cart__user=request.user)
    cart_item.delete()  # deletes the item from cart

    return redirect("home")
def cart(request):
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
            product.cart_item_id=item.id
            product.quantity_in_cart = item.quantity
            product.subtotal_in_cart = item.subtotal()
            # attach first image url (or None if no image)
            first_image = product.productimage_set.first()
            product.image_url = first_image.image.url if first_image else ""
            products.append(product)
    c={
        "cart":products,
        "price":price,
        "log":log,
        "is_logged_in": request.user.is_authenticated,
        "user": request.user if request.user.is_authenticated else None,
    }
    return render(request,"cart.html",c)
def remove_from_cart1(request, item_id):
    if not request.user.is_authenticated:
        return redirect("login")

    cart_item = get_object_or_404(CartItem, product_id=item_id, cart__user=request.user)
    cart_item.delete()  # deletes the item from cart

    return redirect("cart")