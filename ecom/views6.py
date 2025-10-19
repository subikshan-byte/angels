import razorpay
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.utils import timezone
from .models import Product, Order, OrderItem, Coupon, OrderOTP


# -------------------- BUY NOW --------------------
@csrf_exempt
@login_required
def buy_now(request, slug):
    product = get_object_or_404(Product, slug=slug)
    discount = 0
    total_amount = product.price
    quantity = int(request.POST.get("quantity", 1))

    if request.method == "POST":
        coupon_code = request.POST.get("coupon", "").strip().upper()
        address = request.POST.get("address", "").strip()

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

        total_amount = total_amount * quantity
        razorpay_amount = int(total_amount * 100)

        # --- Razorpay Order ---
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save updated address if provided
        if address:
            profile = request.user.userprofile
            profile.address = address
            profile.save()

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


# -------------------- PAYMENT SUCCESS --------------------
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

    # --- Create Order Item ---
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price
    )

    # --- Generate and Send OTP ---
    otp_code = str(random.randint(100000, 999999))
    otp_obj, _ = OrderOTP.objects.update_or_create(
        user=request.user,
        order=order,
        defaults={"otp": otp_code, "created_at": timezone.now(), "verified": False},
    )

    send_mail(
        subject="Your Order Verification OTP",
        message=f"Dear {request.user.first_name}, your OTP for order #{order.id} is {otp_code}. It expires in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
    )

    messages.info(request, "Payment successful! Please verify your order with the OTP sent to your email.")
    return redirect("verify_order_otp")


# -------------------- VERIFY ORDER OTP --------------------
from django.http import JsonResponse
from django.http import JsonResponse
import json
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from .models import OrderOTP

from django.http import JsonResponse
import json

@login_required
@csrf_exempt
def verify_order_otp(request):
    """
    AJAX-based OTP verification for checkout.
    Returns JSON {status: "verified"} or {status: "invalid"}.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            entered_otp = data.get("otp")
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid request format"})

        otp_obj = OrderOTP.objects.filter(user=request.user).last()
        if not otp_obj:
            return JsonResponse({"status": "no_otp", "message": "No OTP found"})

        # Verify OTP
        if otp_obj.otp == entered_otp and otp_obj.is_valid():
            otp_obj.verified = True
            otp_obj.save()
            if otp_obj.order:
                otp_obj.order.status = "confirmed"
                otp_obj.order.save()
            return JsonResponse({"status": "verified"})
        else:
            return JsonResponse({"status": "invalid"})

    # If accessed directly via browser, show normal page
    otp_obj = OrderOTP.objects.filter(user=request.user).last()
    return render(request, "verify_order_otp.html", {"otp_obj": otp_obj})






# -------------------- OPTIONAL: COD SUPPORT --------------------
@login_required
def cod_order(request, slug):
    product = get_object_or_404(Product, slug=slug)
    order = Order.objects.create(
        user=request.user,
        status="pending",
        payment_id="COD",
        address=request.user.userprofile.address
    )
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    messages.success(request, f"Your COD order #{order.id} has been placed successfully!")
    return redirect("myaccount")


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
from django.http import JsonResponse
import json

@login_required
def send_checkout_otp(request):
    """Send OTP before payment via AJAX"""
    if request.method == "POST":
        otp_code = str(random.randint(100000, 999999))
        otp_obj, _ = OrderOTP.objects.update_or_create(
            user=request.user,
            defaults={
                "otp": otp_code,
                "created_at": timezone.now(),
                "verified": False,
            },
        )

        send_mail(
            subject="Your Order Verification OTP",
            message=f"Dear {request.user.first_name}, your OTP is {otp_code}. It will expire in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
        )

        return JsonResponse({"status": "sent"})

    return JsonResponse({"status": "error"}, status=400)
