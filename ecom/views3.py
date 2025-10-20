from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Case, When, Value, IntegerField, Count, Q
from rapidfuzz import fuzz
import re, unicodedata
from .models import Cart, CartItem, Product, Category, Size, UserProfile
from .views import get_product_data1


def search(request, s):
    # --- DETERMINE QUERY INPUT ---
    if s == "0":
        query = request.GET.get("q", "").strip()
    elif s != "100":
        query = s.strip()
    else:
        query = ""

    sort_by = request.GET.get("SortBy", "manual")
    category_filter = request.GET.get("category")
    brand_filter = request.GET.get("brand")
    stock_filter = request.GET.get("stock")
    size_filter = request.GET.get("size")

    results, same_category_products, same_main_category_diff_products = [], [], []

    # --- NORMALIZER -----------------------------------------------------
    def normalize(text):
        text = str(text or "").lower()
        text = text.replace("&", "and").replace("–", "-").replace("—", "-").replace("\xa0", " ")
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r"[^a-z0-9]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    if query:
        query_norm = normalize(query)

        # --- SCORING -----------------------------------------------------
        def score_product(p):
            name = normalize(p.p_name)
            brand = normalize(p.brand_name)
            category = normalize(p.category.c_name)
            combined = f"{name} {brand} {category}"

            name_ratio = fuzz.token_sort_ratio(query_norm, name)
            brand_ratio = fuzz.token_sort_ratio(query_norm, brand)
            combined_ratio = fuzz.partial_ratio(query_norm, combined)

            return max(name_ratio, brand_ratio, combined_ratio), name_ratio, brand_ratio

        # --- CLASSIFY RESULTS --------------------------------------------
        result1, result2, result3 = [], [], []

        for p in Product.objects.all():
            score, name_ratio, brand_ratio = score_product(p)

            if name_ratio >= 90 or score >= 90:
                result1.append(p)
            elif brand_ratio >= 85:
                result2.append(p)
            elif score >= 75:
                result3.append(p)

        # --- ORDER RESULTS -----------------------------------------------
        def order_key(p):
            n = normalize(p.p_name)
            b = normalize(p.brand_name)
            return 0 if n == query_norm else (1 if b == query_norm else 2)

        result1.sort(key=order_key)
        result2.sort(key=order_key)
        result3.sort(key=order_key)

        combined_results = result1 + result2 + result3
        matched_ids = [p.p_id for p in combined_results]

        if matched_ids:
            preserve_order = Case(
                *[When(p_id=pid, then=Value(pos)) for pos, pid in enumerate(matched_ids)],
                output_field=IntegerField(),
            )

            filtered_products = (
                Product.objects.filter(p_id__in=matched_ids)
                .annotate(_order=preserve_order)
                .order_by("_order")
            )
            filtered_products.query.clear_ordering(force=True)
            results = get_product_data1(filtered_products)
        else:
            results = []
    else:
        # Default: all products if no query
        filtered_products = Product.objects.all()
        results = get_product_data1(filtered_products)

    # --- APPLY FILTERS ---
    filtered_products = Product.objects.filter(p_id__in=[r["p_id"] for r in results])

    if category_filter:
        filtered_products = filtered_products.filter(category__c_name__iexact=category_filter)

    if brand_filter:
        filtered_products = filtered_products.filter(brand_name__iexact=brand_filter)

    if stock_filter in ["in stock", "out of stock"]:
        filtered_products = filtered_products.filter(stock_status=stock_filter)

    if size_filter:
        filtered_products = filtered_products.filter(size__size=size_filter)

    if sort_by == "In Stock":
        filtered_products = filtered_products.filter(stock_status="In stock")
    elif sort_by == "Out of Stock":
        filtered_products = filtered_products.filter(stock_status="Out of stock")
    if('100' in s):
        u=s.split(" ")
        if(u[1]=="size"):
            # Fetch all products you want to check
            products = Product.objects.all()

# Size you want to filter
            size_to_filter = u[2]  # e.g., "M"

# Filter in Python
            filtered_products = [
    p for p in products 
    if size_to_filter in [s.size for s in p.size_set.all()]
]





        else:
            filtered_products = filtered_products.filter(brand_name__iexact=u[2])

    u=s.split(" ")
    # --- SORTING ---
    sort_mapping = {
        'manual': None,
        'best-selling': '-where',   # uses your Product.where field
        'title-ascending': 'p_name',
        'title-descending': '-p_name',
        'price-ascending': 'price',
        'price-descending': '-price',
        'created-descending': '-p_id',
        'created-ascending': 'p_id',
    }
    if sort_mapping.get(sort_by):
        filtered_products = filtered_products.order_by(sort_mapping[sort_by])

    # Convert final products back to dicts
    results = get_product_data1(filtered_products)
    t_brands = Product.objects.values_list("brand_name", flat=True).distinct()
    t_category = Product.objects.values_list("category", flat=True).distinct()
    t_brands = Product.objects.values_list("brand_name", flat=True).distinct()


    brands_with_counts = (
    Product.objects.values("brand_name")
    .annotate(total=Count("p_id"))
    .order_by("brand_name")
)
    
    category_with_counts = (
    Product.objects.values("category")
    .annotate(total=Count("p_id")).order_by("category")
)
    for i in category_with_counts:
        i["category"]=Category.objects.get(c_id=i["category"])
    size_counts = (
    Size.objects.values("size")
    .annotate(total=Count("sid"))
    .order_by("size")
)

    brands_with_counts = (
    Product.objects.values("brand_name")
    .annotate(total=Count("p_id"))
    .order_by("brand_name")
)
    stock_counts = (
    Product.objects.values("category__c_name")
    .annotate(total=Count("p_id"))
    .order_by("category__c_name")
)
    selected_brands = request.GET.getlist("brand")
    selected_sizes = request.GET.getlist("size")
    products = []
    price=0
    log='0'
    if not request.user.is_authenticated:
        log='1'
    else:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        
        for item in cart_items:
            product = item.product
            # attach quantity and subtotal
            price+=item.quantity*product.price
            product.quantity_in_cart = item.quantity
            product.subtotal_in_cart = item.subtotal()
            # attach first image url (or None if no image)
            first_image = product.productimage_set.first()
            product.image_url = first_image.image.url if first_image else ""
            products.append(product)
    context = {
        'query': query,
        'results': results,
        'same_category_products': same_category_products,
        'same_main_category_diff_products': same_main_category_diff_products,
        'sort_by': sort_by,
        "brand_list":brands_with_counts,
        "category_list":category_with_counts,
        "size1":size_counts,
        "stock_counts":stock_counts,
        "selected_size":selected_sizes,
        "selected_brands":selected_brands,
        'h':filtered_products,
        "cart":products,
        "price":price,
        "log":log,
        "is_logged_in": request.user.is_authenticated,
        "user": request.user if request.user.is_authenticated else None,
        


    }

    return render(request, 'shop.html', context)
