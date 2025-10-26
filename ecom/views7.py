import razorpay, random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Cart, Product, Order,CartItem, OrderItem, Coupon, UserProfile
from django.shortcuts import redirect
from .models import UserProfile
from django.contrib import messages
from django.shortcuts import redirect
from ecom.models import UserProfile

def check_userprofile_complete(request):
    """Checks if user's email, mobile, address, and zip_code in UserProfile are filled."""
    user = request.user

    if not user.is_authenticated:
        messages.warning(request, "Please log in to continue.")
        return redirect("login")

    # Always ensure profile exists
    profile, created = UserProfile.objects.get_or_create(user=user)

    # ✅ Pull all values from UserProfile (not from User)
    mobile = (getattr(profile, "mobile", "") or "").strip()
    address = (getattr(profile, "address", "") or "").strip()
    zip_code = (getattr(profile, "zip_code", getattr(profile, "zipcode", "")) or "").strip()

    print("------ DEBUG PROFILE CHECK ------")
    print("Mobile:", repr(mobile))
    print("Address:", repr(address))
    print("Zip Code:", repr(zip_code))
    print("--------------------------------")

    # ✅ Check if any are missing or empty
    if  not mobile or not address or not zip_code:
        messages.warning(request, "Please complete your profile before proceeding.")
        return redirect("/myaccount")

    # ✅ Everything is fine — continue normally
    return None









# ------------------ CHECKOUT PAGE ------------------
@login_required
def cart_checkout(request):
    check = check_userprofile_complete(request)
    if check:  # means function returned a redirect
        return check

    # ✅ All profile fields complete — continue checkout
    ...

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

    data = json.loads(request.body.decode("utf-8"))
    coupon_code = data.get("coupon")
    
    total_amount = sum(item.product.price * item.quantity for item in cart_items)
    
    if coupon_code:
        try:
            cpn = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if hasattr(cpn, "discount_percent") and cpn.discount_percent:
                discount = (total_amount * cpn.discount_percent) / 100
            else:
                discount = getattr(cpn, "discount_amount", 0)
            total_amount -= discount
        except Coupon.DoesNotExist:
            pass


    # Create order
    cart_items =CartItem.objects.filter(cart__user=request.user)


    # ✅ Step 2: Calculate total price
    cart_total = sum(item.product.price * item.quantity for item in cart_items)

    order = Order.objects.create(
    user=request.user,
    
    address=address,
    payment_method='cod'
)


    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    cart.items.all().delete()
    cart_items.delete()
    # Remove OTP verification
    request.session.pop("otp_verified", None)

    return JsonResponse({"status": "placed", "redirect": "/myaccount"})


# ------------------ CREATE RAZORPAY ORDER (AJAX) ------------------
import json
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Sum
from .models import CartItem

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
@csrf_exempt
def create_razorpay_order_cart(request):
    if request.method == 'POST':
        try:
            cart_items = CartItem.objects.filter(cart__user=request.user)
            total_amount = sum(item.product.price * item.quantity for item in cart_items)
            amount_paise = int(total_amount * 100)

            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': '1'
            })

            return JsonResponse({
                'status': 'created',
                'order_id': razorpay_order['id'],
                'amount': amount_paise,
                'key': settings.RAZORPAY_KEY_ID
            })
        except Exception as e:
            print("Error creating Razorpay order for cart:", e)
            return JsonResponse({'status': 'error', 'message': 'Error creating Razorpay order.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)



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
