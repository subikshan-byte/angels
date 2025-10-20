import razorpay, random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Cart, Product, Order, OrderItem, Coupon, UserProfile

# ------------------ CHECKOUT PAGE ------------------
@login_required
def cart_checkout(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()

    if not items.exists():
        return redirect("cart")

    total_amount = sum(item.subtotal() for item in items)
    total_paise = int(total_amount * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": total_paise,
        "currency": "INR",
        "payment_capture": "1"
    })

    profile = UserProfile.objects.get(user=request.user)

    return render(request, "checkout1.html", {
        "items": items,
        "total_amount": total_amount,
        "order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "callback_url": "/payment/success-cart/",
        "profile": profile,
    })


# ------------------ SEND OTP ------------------
@login_required
def send_checkout_otp(request):
    if request.method == "POST":
        otp = random.randint(100000, 999999)
        request.session["checkout_otp"] = str(otp)

        send_mail(
            subject="Your Checkout OTP",
            message=f"Your OTP for checkout verification is {otp}. It will expire in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )
        return JsonResponse({"status": "sent"})
    return JsonResponse({"status": "error"}, status=400)


# ------------------ VERIFY OTP ------------------
@login_required
def verify_order_otp(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body.decode("utf-8"))
        user_otp = data.get("otp")
        session_otp = request.session.get("checkout_otp")

        if not session_otp:
            return JsonResponse({"status": "no_otp"})

        if str(user_otp) == session_otp:
            del request.session["checkout_otp"]
            request.session["otp_verified"] = True
            return JsonResponse({"status": "verified"})
        return JsonResponse({"status": "invalid"})
    return HttpResponseBadRequest()


# ------------------ APPLY COUPON ------------------
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart, Coupon
import json
from datetime import date

@login_required
def apply_coupon(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            code = data.get("coupon", "").strip()

            if not code:
                return JsonResponse({"status": "invalid", "message": "Coupon code cannot be empty."})

            # Get the user's cart
            cart = Cart.objects.get(user=request.user)
            items = cart.items.all()
            if not items.exists():
                return JsonResponse({"status": "invalid", "message": "Your cart is empty."})

            total = sum(item.subtotal() for item in items)

            # ✅ FIXED: using `active` instead of `is_active`
            try:
                coupon = Coupon.objects.get(code__iexact=code, active=True)

                # Check expiry
                if coupon.expiry_date and coupon.expiry_date < date.today():
                    return JsonResponse({"status": "invalid", "message": "This coupon has expired."})

                # Apply percentage discount if field is present
                if hasattr(coupon, "discount_percent") and coupon.discount_percent:
                    discount = (total * coupon.discount_percent) / 100
                else:
                    discount = getattr(coupon, "discount_amount", 0)

                new_total = max(total - discount, 0)

                return JsonResponse({
                    "status": "ok",
                    "total": round(new_total, 2),
                    "message": f"Coupon '{coupon.code}' applied successfully! You saved ₹{round(discount,2)}."
                })

            except Coupon.DoesNotExist:
                return JsonResponse({"status": "invalid", "message": "Invalid or expired coupon."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method."})


# ------------------ SAVE ADDRESS (AJAX from Edit) ------------------
@login_required
def edit(request):
    import json
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        address = data.get("address")
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if address:
            profile.address = address
            profile.save()
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error"})
    return HttpResponseBadRequest()


# ------------------ PLACE COD ORDER ------------------
@login_required
def place_cod_order(request):
    from django.db.models import Sum
    import json
    data = json.loads(request.body.decode("utf-8"))
    if not request.session.get("otp_verified"):
        return JsonResponse({"status": "error", "message": "OTP not verified"})

    address = data.get("address")
    coupon = data.get("coupon")

    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()
    if not items.exists():
        return JsonResponse({"status": "error", "message": "Cart is empty"})

    total_amount = sum(item.subtotal() for item in items)
    if coupon:
        try:
            cpn = Coupon.objects.get(code__iexact=coupon, is_active=True)
            total_amount -= cpn.discount_amount
        except Coupon.DoesNotExist:
            pass

    # Create order
    cart_total = cart_items.aggregate(total=Sum('total_price'))['total'] or 0
    order = Order.objects.create(
    user=request.user,
    total_price=cart_total,
    address=address,
    payment_mode='COD'
)


    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    cart.items.all().delete()

    # Remove OTP verification
    request.session.pop("otp_verified", None)

    return JsonResponse({"status": "placed", "redirect": "/myaccount/"})


# ------------------ CREATE RAZORPAY ORDER (AJAX) ------------------
@login_required
def create_razorpay_order(request):
    import json
    data = json.loads(request.body.decode("utf-8"))
    address = data.get("address")
    coupon = data.get("coupon")

    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()
    if not items.exists():
        return JsonResponse({"status": "error", "message": "Cart is empty"})

    total_amount = sum(item.subtotal() for item in items)
    if coupon:
        try:
            cpn = Coupon.objects.get(code__iexact=coupon, is_active=True)
            total_amount -= cpn.discount_amount
        except Coupon.DoesNotExist:
            pass

    total_paise = int(total_amount * 100)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    order = client.order.create({"amount": total_paise, "currency": "INR", "payment_capture": "1"})

    request.session["pending_order"] = {
        "address": address,
        "total_amount": total_amount,
        "order_id": order["id"],
    }

    return JsonResponse({
        "status": "created",
        "order_id": order["id"],
        "amount": total_paise,
        "key": settings.RAZORPAY_KEY_ID,
    })


# ------------------ PAYMENT SUCCESS (RAZORPAY) ------------------
@csrf_exempt
@login_required
def payment_success_cart(request):
    payment_id = request.POST.get("razorpay_payment_id") or request.GET.get("razorpay_payment_id")
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()

    pending = request.session.get("pending_order", {})
    address = pending.get("address", request.user.userprofile.address)
    total = pending.get("total_amount", sum(i.subtotal() for i in items))

    if not items.exists():
        return redirect("cart")

    order = Order.objects.create(
        user=request.user,
        status="paid",
        payment_id=payment_id,
        address=address,
        total=total,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    cart.items.all().delete()
    request.session.pop("pending_order", None)
    request.session.pop("otp_verified", None)

    return redirect("myaccount")
