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
import logging
logger = logging.getLogger(__name__)

def check_userprofile_complete(request):
    """Safely checks if user's profile is complete and avoids I/O crashes."""
    user = request.user

    if not user.is_authenticated:
        messages.warning(request, "Please log in to continue.")
        return redirect("login")

    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
    except OSError as e:
        # This captures disk/storage-related I/O errors
        logger.exception(f"I/O error while fetching/creating UserProfile for user {user.id}: {e}")
        messages.error(request, "Temporary profile issue. Please try again later.")
        return redirect("myaccount")
    except Exception as e:
        logger.exception(f"Unexpected error in check_userprofile_complete: {e}")
        messages.error(request, "Something went wrong while checking your profile.")
        return redirect("myaccount")

    # ✅ Pull all values safely
    mobile = (getattr(profile, "mobile", "") or "").strip()
    address = (getattr(profile, "address", "") or "").strip()
    zip_code = (getattr(profile, "zip_code", getattr(profile, "zipcode", "")) or "").strip()

    if not mobile or not address or not zip_code:
        messages.warning(request, "Please complete your profile before proceeding.")
        return redirect("/myaccount")

    return None










# ------------------ CHECKOUT PAGE ------------------
@csrf_exempt
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
    log='0'
    if not request.user.is_authenticated:
        log='1'
    if(total_amount<2000):
        total_amount+=100;

    return render(request, "checkout1.html", {
        "items": items,
        "total_amount": total_amount,
        "order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "callback_url": "/payment/success-cart/",
        "profile": profile,
        
        "log":log,
    })


# ------------------ SEND OTP ------------------
@csrf_exempt
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

@csrf_exempt
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
from datetime import date
import json

@login_required
def apply_coupon(request):
    print("Received coupon apply request:", request.body)

    if request.method == "POST":
        try:
            # Parse JSON data
            data = json.loads(request.body.decode("utf-8"))
            code = (data.get("coupon") or "").strip()

            if not code:
                return JsonResponse({
                    "status": "invalid",
                    "message": "Please enter a coupon code."
                })

            # Get user's cart
            cart = Cart.objects.filter(user=request.user).first()
            if not cart:
                return JsonResponse({
                    "status": "invalid",
                    "message": "Your cart is empty."
                })

            items = cart.items.all()
            if not items.exists():
                return JsonResponse({
                    "status": "invalid",
                    "message": "Your cart is empty."
                })

            total = sum(item.subtotal() for item in items)

            # ✅ Safely get active coupon
            coupon = Coupon.objects.filter(code__iexact=code, active=True).first()
            if not coupon:
                return JsonResponse({
                    "status": "invalid",
                    "message": "Invalid or inactive coupon."
                })

            # ✅ Check expiry
            if coupon.expiry_date and coupon.expiry_date < date.today():
                return JsonResponse({
                    "status": "invalid",
                    "message": "This coupon has expired."
                })

            # ✅ Calculate discount
            if hasattr(coupon, "discount_percent") and coupon.discount_percent:
                discount = (total * coupon.discount_percent) / 100
            else:
                discount = getattr(coupon, "discount_amount", 0)

            new_total = max(total - discount, 0)
            if(total<2000):
                new_total+=100
            # ✅ Store in session for later use (like order or Razorpay)
            request.session["applied_coupon"] = {
                "code": coupon.code,
                "discount": float(discount),
                "new_total": float(new_total)
            }
            
            # ✅ Return JSON response
            return JsonResponse({
                "status": "ok",
                "total": round(new_total, 2),
                "message": f"Coupon '{coupon.code}' applied successfully! You saved ₹{round(discount,2)}.+if total price is more than 2000 .then not applicable +₹100 for delivery charge"
            })

        except Exception as e:
            print("Error applying coupon:", e)
            return JsonResponse({
                "status": "error",
                "message": "Something went wrong while applying the coupon."
            })

    # If method is not POST
    return JsonResponse({
        "status": "error",
        "message": "Invalid request method."
    })



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


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import json
from .models import Cart, CartItem, Order, OrderItem, Coupon
@csrf_exempt
@login_required
def place_cod_order(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."})

    # Parse JSON from frontend
    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"status": "error", "message": "Invalid JSON data."})

    # Ensure OTP is verified
    if not request.session.get("otp_verified"):
        return JsonResponse({"status": "error", "message": "OTP not verified."})

    address = data.get("address", "").strip()
    coupon_code = data.get("coupon", "").strip()

    # Fetch user's cart
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."})

    cart_items = CartItem.objects.filter(cart=cart)
    if not cart_items.exists():
        return JsonResponse({"status": "error", "message": "Your cart is empty."})

    # Calculate total amount
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    # Apply coupon if any
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if coupon.is_valid():
                discount = (total_amount * coupon.discount_percent) / 100
                total_amount -= discount
        except Coupon.DoesNotExist:
            pass

    # Create Order
    order = Order.objects.create(
        user=request.user,
        address=address,
        payment_method='cod',
        status='pending'  # Matches your model choices
    )

    # Create Order Items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    # Clear the cart
    cart_items.delete()
    cart.delete()

    # Remove OTP flag
    request.session.pop("otp_verified", None)

    # Return success response
    return JsonResponse({
        "status": "placed",
        "redirect": reverse("myaccount")  # or "/myaccount"
    })




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

import json
import razorpay
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Cart, CartItem, Order, OrderItem, Coupon
@csrf_exempt
@login_required
def create_razorpay_order_cart(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method."})

    # ✅ OTP verification
    if not request.session.get("otp_verified"):
        return JsonResponse({"status": "error", "message": "OTP not verified."})

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"status": "error", "message": "Invalid JSON."})

    coupon_code = data.get("coupon", "").strip()
    address = data.get("address", "").strip()

    # ✅ Fetch cart and items
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Cart not found."})

    cart_items = CartItem.objects.filter(cart=cart)
    if not cart_items.exists():
        return JsonResponse({"status": "error", "message": "Cart empty."})

    # ✅ Calculate total
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    # ✅ Apply coupon
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            if coupon.is_valid():
                discount = (total_amount * coupon.discount_percent) / 100
                total_amount -= discount
        except Coupon.DoesNotExist:
            pass

    amount_paise = int((total_amount+100) * 100)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })

        print("✅ Razorpay order created:", razorpay_order)

        # ✅ Store pending order details in session
        request.session["pending_order"] = {
            "razorpay_order_id": razorpay_order["id"],
            "total_amount": float(total_amount),
            "address": address,
        }

        # ✅ Respond to frontend JS
        return JsonResponse({
            "status": "created",
            "key": settings.RAZORPAY_KEY_ID,
            "amount": amount_paise,
            "order_id": razorpay_order["id"]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Razorpay order creation error:", e)
        return JsonResponse({"status": "error", "message": str(e)})


# ------------------ PAYMENT SUCCESS (RAZORPAY) ------------------
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Cart, Order, OrderItem

@csrf_exempt
@login_required
def payment_success_cart(request):
    payment_id = request.GET.get("razorpay_payment_id")
    pending = request.session.get("pending_order", {})

    if not payment_id:
            return redirect("cart")

    address = pending.get("address", "")
    total_amount = pending.get("total_amount", 0)

    # ✅ Create paid order
    order = Order.objects.create(
        user=request.user,
        address=address,
        payment_method='online',
        status='paid',
        payment_id=payment_id,
    )

    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    # ✅ Cleanup
    cart_items.delete()
    cart.delete()
    request.session.pop("otp_verified", None)
    request.session.pop("pending_order", None)

    return redirect("myaccount")
