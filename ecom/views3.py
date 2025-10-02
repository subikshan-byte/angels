from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import Cart, CartItem, Product,Category,Size, UserProfile
from .views import get_product_data1
from rapidfuzz import fuzz
from django.db.models import Count


def search(request,s):
    if(s=='0'):
        query = request.GET.get('q', '').strip()
    if(s!='0' and s!='100'):
        query=s.strip()
    sort_by = request.GET.get("SortBy", "manual")
    category_filter = request.GET.get("category")
    brand_filter = request.GET.get("brand")
    stock_filter = request.GET.get("stock")
    size_filter = request.GET.get("size")

    results = []
    same_category_products = []
    same_main_category_diff_products = []

    # Fetch all products (we’ll filter later)
    candidates = Product.objects.all()

    if query:
        matched_products = []

        # Hierarchy: only selected fields
        hierarchy = [
            ("p_name", 85),
            ("small_title", 80),
            ("brand_name", 75),
            ("category__c_name", 75),
            ("main_category_diff", 70),
        ]

        for field, threshold in hierarchy:
            for product in candidates:
                # Extract value depending on field
                if field == "category__c_name":
                    value = product.category.c_name
                else:
                    value = getattr(product, field, "")

                if fuzz.partial_ratio(query.lower(), str(value).lower()) >= threshold:
                    if product not in matched_products:
                        matched_products.append(product)

        # Main search results
        results = get_product_data1(matched_products)

        if matched_products:
            first_product = matched_products[0]

            # Related products - same category
            same_category_products = Product.objects.filter(
                category=first_product.category
            ).exclude(p_id=first_product.p_id)

            # Related products - same main_category_diff
            same_main_category_diff_products = Product.objects.filter(
                main_category_diff=first_product.main_category_diff
            ).exclude(p_id=first_product.p_id)

            # Convert to dicts
            same_category_products = get_product_data1(same_category_products)
            same_main_category_diff_products = get_product_data1(same_main_category_diff_products)

            # ---- Deduplicate across all results ----
            seen_ids = set()
            unique_results = []
            for group in [results, same_category_products, same_main_category_diff_products]:
                clean_group = []
                for prod in group:
                    if prod["p_id"] not in seen_ids:
                        seen_ids.add(prod["p_id"])
                        clean_group.append(prod)
                if group is results:
                    results = clean_group
                elif group is same_category_products:
                    same_category_products = clean_group
                else:
                    same_main_category_diff_products = clean_group
    else:
        # If no query, just show all products
        results = get_product_data1(candidates)

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
