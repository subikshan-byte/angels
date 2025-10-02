import razorpay
from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem
from django.conf import settings


@login_required
def buy_now(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        total_amount = int(product.price * quantity * 100)  # Razorpay needs paise

        # Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create Razorpay Order
        razorpay_order = client.order.create({
            "amount": total_amount,
            "currency": "INR",
            "payment_capture": "1"
        })
        total_amount/=100
        # Pass details to checkout template
        return render(request, "checkout.html", {
            "product": product,
            "quantity": quantity,
            "total_amount": total_amount,
            "order_id": razorpay_order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            # IMPORTANT: pass slug & qty in success URL
            "callback_url": f"/payment/success/?product_slug={product.slug}&quantity={quantity}"
        })

    return redirect("product", p=slug)  # fallback if GET request


# ---------------- SUCCESS VIEW ----------------

@csrf_exempt
@login_required
def payment_success(request):
    product_slug = request.GET.get("product_slug")
    quantity = int(request.GET.get("quantity", 1))
    payment_id = request.POST.get("razorpay_payment_id") or request.GET.get("razorpay_payment_id")

    product = get_object_or_404(Product, slug=product_slug)

    # Create Order
    order = Order.objects.create(
        user=request.user,
        status="paid",
        payment_id=payment_id
    )

    # Create OrderItem
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price
    )

    return render(request, "success.html", {
        "order": order,
        "product": product,
        "quantity": quantity,
        "total": order.total_price(),
    })
from django.shortcuts import redirect, get_object_or_404
from .models import CartItem

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from .models import CartItem

def update_cart_quantity(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        quantity = request.POST.get("quantity")

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            quantity = cart_item.quantity  # fallback to current quantity

        if action == "increase":
            cart_item.quantity = quantity + 1
        elif action == "decrease" and quantity > 1:
            cart_item.quantity = quantity - 1
        else:
            cart_item.quantity = quantity

        cart_item.save()
        return HttpResponse(action)

    return redirect('cart')  # redirect to cart page

