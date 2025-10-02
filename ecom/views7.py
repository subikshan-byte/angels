import razorpay
from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Cart, Product, Order, OrderItem
from django.conf import settings
@login_required
def cart_checkout(request):
    # Get user's cart
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()

    if not items.exists():
        return redirect("cart")  # Nothing to checkout

    total_amount = int(sum(item.subtotal() for item in items) * 100)  # in paise

    # Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    razorpay_order = client.order.create({
        "amount": total_amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    return render(request, "checkout1.html", {
        "items": items,
        "total_amount": total_amount / 100,  # pass in rupees for display
        "order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "callback_url": "/payment/success-cart/"  # success URL for cart checkout
    })
@csrf_exempt
@login_required
def payment_success_cart(request):
    payment_id = request.POST.get("razorpay_payment_id") or request.GET.get("razorpay_payment_id")
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()

    if not items.exists():
        return redirect("cart")

    # Create Order
    order = Order.objects.create(
        user=request.user,
        status="paid",
        payment_id=payment_id,
        address=request.user.userprofile.address
    )

    # Move all cart items to order items
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    # Clear cart
    cart.items.all().delete()

    return redirect("myaccount")
