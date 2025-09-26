
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import render

from ecom.models import Product

def shop(request):
    query = request.GET.get("q", "")
    selected_brands = request.GET.getlist("brand")   # multiple checkboxes
    selected_sizes = request.GET.getlist("size")     # multiple checkboxes

    # 🔎 Step 1: Base search filter
    products = Product.objects.all()
    if query:
        products = products.filter(
            Q(p_name__icontains=query) |
            Q(brand_name__icontains=query)
        )

    # 🔎 Step 2: Apply brand filter (if any checkbox selected)
    if selected_brands:
        products = products.filter(brand_name__in=selected_brands)

    # 🔎 Step 3: Apply size filter
    if selected_sizes:
        products = products.filter(size__size__in=selected_sizes)

    # 🔎 Step 4: Sidebar data (only from current search results!)
    brand_list = (
        products.values("brand_name")
        .annotate(total=Count("p_id"))
        .order_by("brand_name")
    )
    size1 = (
        products.values("size__size")
        .annotate(total=Count("p_id"))
        .order_by("size__size")
    )

    return render(request, "shop.html", {
        "search_list": products,
        "brand_list": brand_list,
        "size1": size1,
        "selected_brands": selected_brands,
        "selected_sizes": selected_sizes,
        "query": query,
    })
