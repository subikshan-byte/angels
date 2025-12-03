import razorpay
import random
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt  # only used on views that intentionally need it
from django.core.mail import send_mail
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Product, Order, OrderItem, Coupon, OrderOTP, UserProfile
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



# -------------------- BUY NOW (kept for legacy use; still works) --------------------
@login_required
def buy_now(request, slug):
    if not request.user.is_authenticated:
        return redirect("login")

    redirect_response = check_userprofile_complete(request)
    if redirect_response:
        return redirect_response 
    """
    This view is kept for compatibility: in previous code you used POST to buy_now to render checkout.
    We now favour AJAX endpoints for creating payments.
    It still supports coupon apply when posting normally.
    """
    product = get_object_or_404(Product, slug=slug)
    discount = Decimal('0')
    total_amount = Decimal(product.price or 0)
    quantity = int(request.POST.get("quantity", 1))
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    # If JSON request (AJAX coupon apply), accept JSON payload
    if request.method == "POST":
        # handle JSON or form
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        coupon_code = data.get("coupon", "").strip() if data else ""
        action = data.get("action") if isinstance(data, dict) else request.POST.get("action")

        if action == 'apply_coupon' and coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code.upper())
                if coupon.is_valid():
                    discount = (Decimal(product.price) * Decimal(coupon.discount_percent)) / Decimal(100)
                    total_amount = (Decimal(product.price) - discount) * Decimal(quantity)
                    return JsonResponse({
                        "status": "ok",
                        "discount": float(discount),
                        "total_amount": float(total_amount),
                        "message": f"{coupon.discount_percent}% discount applied"
                        
                    })
                else:
                    return JsonResponse({"status": "error", "message": "Coupon expired or inactive."})
            except Coupon.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Invalid coupon code."})

        # legacy: render checkout page if regular HTML POST
        # compute total and create razorpay order server-side for older flow
        coupon_code = request.POST.get("coupon", "").strip().upper()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.is_valid():
                    discount = (Decimal(product.price) * Decimal(coupon.discount_percent)) / Decimal(100)
                    total_amount = (Decimal(product.price) - discount) * Decimal(quantity)
                    messages.success(request, f"{coupon.discount_percent}% discount applied!")
                else:
                    messages.error(request, "Coupon expired or inactive.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")

        total_amount = total_amount * quantity
        razorpay_amount = int(total_amount * 100)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": razorpay_amount,
            "currency": "INR",
            "payment_capture": "1"
        })

        address = request.POST.get("address", "").strip()
        if address:
            profile = request.user.userprofile
            profile.address = address
            profile.save()
        log='0'
        if not request.user.is_authenticated:
           log='1'
        if(total_amount<2000):
            total_amount+=100;
        
        return render(request, "checkout.html", {
            "product": product,
            "quantity": quantity,
            "discount": discount,
            "total_amount": float(total_amount),
            "order_id": razorpay_order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "callback_url": f"/payment/success/?product_slug={product.slug}&quantity={quantity}",
            "profile":profile,
            "log":log,
            
        })

    return redirect("product", p=slug)


# -------------------- PAYMENT SUCCESS (Razorpay posts back here) --------------------
@csrf_exempt
@login_required
def payment_success(request):
    """
    Razorpay sends back the payment_id (via form submission we do in JS).
    This view creates the Order in DB (so we don't create it earlier).
    """
    product_slug = request.GET.get("product_slug")
    quantity = int(request.GET.get("quantity", 1))
    payment_id = request.POST.get("razorpay_payment_id") or request.GET.get("razorpay_payment_id")
    product = get_object_or_404(Product, slug=product_slug)

    # Create Order (payment confirmed by Razorpay)
    order = Order.objects.create(
        user=request.user,
        status="paid",
        payment_id=payment_id,
        payment_method='online',
        address=request.user.userprofile.address
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        price=product.price
    )

    # generate OTP for verification after payment (optional - you already had this behaviour)
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
    return redirect("home")


# -------------------- SEND CHECKOUT OTP (AJAX) --------------------
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import OrderOTP

@login_required
def send_checkout_otp(request):
    try:
        otp = get_random_string(length=6, allowed_chars='0123456789')

        # ✅ Delete any old OTP for this user first
        OrderOTP.objects.filter(user=request.user).delete()

        # ✅ Create new OTP safely
        otp_obj = OrderOTP.objects.create(user=request.user, otp=otp)

        send_mail(
            subject="Your Checkout OTP",
            message=f"Your OTP for checkout is: {otp}",
            from_email="no-reply@zapwaves.com",
            recipient_list=[request.user.email],
            fail_silently=False,
        )

        return JsonResponse({"status": "sent"})

    except Exception as e:
        print("❌ Error sending OTP:", e)
        return JsonResponse({"status": "error", "message": str(e)})



# -------------------- VERIFY ORDER OTP (AJAX) --------------------
@login_required
def verify_order_otp(request):
    """
    Verify OTP sent earlier. Accepts JSON POST {otp: "xxxxxx"}.
    If verified, returns {"status": "verified"}.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            entered_otp = data.get("otp")
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        otp_obj = OrderOTP.objects.filter(user=request.user).last()
        if not otp_obj:
            return JsonResponse({"status": "no_otp", "message": "No OTP found"})

        if otp_obj.otp == entered_otp and otp_obj.is_valid():
            otp_obj.verified = True
            otp_obj.save()
            # don't alter orders here — code that creates orders will set status accordingly
            return JsonResponse({"status": "verified"})
        else:
            return JsonResponse({"status": "invalid"})
    # Fallback: render the existing page if user navigates directly
    otp_obj = OrderOTP.objects.filter(user=request.user).last()
    return render(request, "verify_order_otp.html", {"otp_obj": otp_obj})


# -------------------- CREATE RAZORPAY ORDER (AJAX) --------------------
import json
import razorpay
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Product, Order
from decimal import Decimal

@login_required
def create_razorpay_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            coupon_code = data.get("coupon", "").strip()
            address = data.get("address", "").strip()

            # --- STEP 1: Get product and quantity ---
            product_slug = data.get("product_slug")
            quantity = int(data.get("quantity", 1))

            if not product_slug:
                return JsonResponse({"status": "error", "message": "Product not specified."})

            product = Product.objects.get(slug=product_slug)
            total = Decimal(product.price) * quantity

            # --- STEP 2: Apply coupon (optional) ---
            from .models import Coupon  # only if you have Coupon model
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
                    if hasattr(coupon, "discount_percent"):
                        discount = (total * Decimal(coupon.discount_percent)) / 100
                    else:
                        discount = getattr(coupon, "discount_amount", Decimal(0))
                    total -= discount
                except Coupon.DoesNotExist:
                    pass  # ignore invalid coupons

            # --- STEP 3: Convert amount to paise (Razorpay expects integer) ---
            amount_paise = int((total +100)* 100)

            # --- STEP 4: Initialize Razorpay client ---
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # --- STEP 5: Create Razorpay order ---
            razorpay_order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": "1",
            })

            # --- STEP 6: Return order details to frontend ---
            return JsonResponse({
                "status": "created",
                "order_id": razorpay_order["id"],
                "amount": amount_paise,
                "key": settings.RAZORPAY_KEY_ID,
            })

        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Product not found."})
        except Exception as e:
            # Log the exact error to console
            print("❌ Razorpay order creation failed:", e)
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method."})



# -------------------- PLACE COD ORDER (AJAX) --------------------
@login_required
def place_cod_order(request):
    """
    Called after OTP verification when user chooses COD.
    Expects JSON: { product_slug, quantity, coupon, address }
    Creates Order with payment_method='cod' and returns redirect URL.
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    product_slug = data.get("product_slug")
    quantity = int(data.get("quantity", 1))
    coupon_code = (data.get("coupon") or "").strip().upper()
    address = (data.get("address") or "").strip()

    product = get_object_or_404(Product, slug=product_slug)

    # calculate total with coupon (we store it on order items price)
    total = Decimal(product.price)
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_valid():
                discount = (total * Decimal(coupon.discount_percent)) / Decimal(100)
                total = (total - discount)
            else:
                return JsonResponse({"status": "error", "message": "Coupon expired or inactive."})
        except Coupon.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid coupon."})

    # save address if provided
    if address:
        profile = request.user.userprofile
        profile.address = address
        profile.save()

    # create order & order item
    order = Order.objects.create(
        user=request.user,
        status="pending",
        payment_id="COD",
        payment_method="cod",
        address=address or request.user.userprofile.address
    )

    OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)

    # generate verification OTP for order (optional)
    otp_code = str(random.randint(100000, 999999))
    otp_obj, _ = OrderOTP.objects.update_or_create(
        user=request.user,
        order=order,
        defaults={"otp": otp_code, "created_at": timezone.now(), "verified": False},
    )

    send_mail(
        subject="Your COD Order OTP",
        message=f"Dear {request.user.first_name}, your OTP for COD order #{order.id} is {otp_code}. Please verify to confirm delivery.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
    )

    return JsonResponse({"status": "placed", "redirect": "/myaccount"})



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
from decimal import Decimal
from decimal import Decimal
from django.http import JsonResponse
from .models import Coupon, Product
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from decimal import Decimal
from .models import Coupon, Product

@login_required# temporarily bypass CSRF for testing
def apply_coupon1(request):
    print("=== COUPON API HIT ===", request.method)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"})

    try:
        data = json.loads(request.body.decode("utf-8"))
        print("Payload:", data)
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Bad JSON: {str(e)}"})

    coupon_code = data.get("coupon")
    product_slug = data.get("product_slug")
    quantity = int(data.get("quantity", 1))

    try:
        product = Product.objects.get(slug=product_slug)
    except Product.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Product not found."})

    try:
        coupon = Coupon.objects.get(code=coupon_code, active=True)
    except Coupon.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid coupon."})

    original_total = Decimal(product.price) * quantity
    
    discount = (original_total * coupon.discount_percent/ Decimal(100)) 
    

    final_total = max(Decimal("0.00"), original_total - discount)
    if(final_total<2000):
        final_total+=100
    return JsonResponse({
        "status": "ok",
        "message": f"Coupon '{coupon.code}' applied successfully! You saved ₹{discount:.2f}.if total price is more than 2000 .then not applicable +₹100 for delivery charge",
        "discount": float(discount),
        "original_total": float(original_total),
        "total": float(final_total)
    })



