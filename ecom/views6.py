import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem, Coupon

@login_required
def buy_now(request, slug):
    product = get_object_or_404(Product, slug=slug)
    discount = 0
    total_amount = product.price

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        coupon_code = request.POST.get("coupon", "").strip().upper()

        # --- Coupon Check ---
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid():
                    discount = (product.price * coupon.discount_percent) / 100
                    total_amount = product.price - discount
                    messages.success(request, f"{coupon.discount_percent}% discount applied!")
                else:
                    messages.error(request, "Coupon expired or inactive.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

        # --- Razorpay Calculation ---
        total_amount = total_amount * quantity
        razorpay_amount = int(total_amount * 100)  # convert to paise

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        return render(request, "checkout.html", {
            "product": product,
            "quantity": quantity,
            "discount": discount,
            "total_amount": total_amount,
            "order_id": razorpay_order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "callback_url": f"/payment/success/?product_slug={product.slug}&quantity={quantity}"
        })

    return redirect("product", p=slug)


# ---------------- SUCCESS VIEW ----------------
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.contrib import messages
from .models import OrderOTP

@csrf_exempt
@login_required
def payment_success(request):
    product_slug = request.GET.get("product_slug")
    quantity = int(request.GET.get("quantity", 1))
    payment_id = request.POST.get("razorpay_payment_id") or request.GET.get("razorpay_payment_id")

    product = get_object_or_404(Product, slug=product_slug)

    # --- Create Order ---
    order = Order.objects.create(
        user=request.user,
        status="paid",
        payment_id=payment_id,
        address=request.user.userprofile.address
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price
    )

    # --- OTP Generation ---
    otp_obj, _ = OrderOTP.objects.get_or_create(user=request.user, order=order)
    otp_obj.generate_otp()

    # --- Email OTP ---
    send_mail(
        subject="Your Order Verification OTP",
        message=f"Dear {request.user.first_name}, your OTP for order #{order.id} is {otp_obj.otp}. It will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
    )

    messages.success(request, "Payment successful! OTP sent to your email for order verification.")
    return redirect("verify_order_otp")
@login_required
def verify_order_otp(request):
    otp_obj = OrderOTP.objects.filter(user=request.user).last()

    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        if otp_obj and otp_obj.otp == entered_otp and otp_obj.is_valid():
            otp_obj.verified = True
            otp_obj.save()
            otp_obj.order.status = "confirmed"
            otp_obj.order.save()
            messages.success(request, "Order verified successfully!")
            return redirect("myaccount")
        else:
            messages.error(request, "Invalid or expired OTP.")

    return render(request, "verify_order_otp.html")
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

    return redirect('cart')
