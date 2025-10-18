from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem

@login_required
def order_check(request):
    # Assuming the latest pending order
    order = Order.objects.filter(user=request.user, status='pending').last()
    if not order:
        messages.error(request, "No pending order found.")
        return redirect("home")

    order_items = order.items.all()
    subtotal = sum(item.subtotal() for item in order_items)
    discount = 0
    total = subtotal

    if request.method == "POST":
        if "apply_coupon" in request.POST:
            coupon_code = request.POST.get("coupon", "")
            if coupon_code == "12345":
                discount = subtotal * 0.10
                total = subtotal - discount
                messages.success(request, "Coupon applied successfully (10% off).")
            else:
                messages.error(request, "Invalid coupon code.")
        elif "proceed_later" in request.POST:
            messages.info(request, "You can return later to complete your order.")
            return redirect("home")

    context = {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
    }
    return render(request, "order_check.html", context)
