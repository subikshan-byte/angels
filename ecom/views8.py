from django.shortcuts import render
def contact(request):
    return render(request,"contact.html")
def about(request):
    return render(request,"about.html")
def privacy(request):
    return render(request,"privacy.html")
def paymentrazor(request):
    return render(request,"payment.html")
def sitemap(request):
    return render(request,"sitemap.xml")
