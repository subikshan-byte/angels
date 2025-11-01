from django.shortcuts import render
from .models import Cart, Product, Order,CartItem, OrderItem, Coupon, UserProfile
def contact(request):
    log='0'
    price=0;
    if not request.user.is_authenticated:
        log='1'
    return render(request,"contact.html",{"log":log,})
def about(request):
    log='0'
    if not request.user.is_authenticated:
        log='1'
 
    return render(request,"about.html",{"log":log,})
def privacy(request):
    return render(request,"privacy.html")
def paymentrazor(request):
    return render(request,"payment.html")
def sitemap(request):
    return render(request,"sitemap.xml")
def robots(request):
    return render(request,"robots.txt")
