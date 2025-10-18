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
    matched_products=[]
    same_main_category_diff_products = []

    # Fetch all products (we’ll filter later)
    candidates = Product.objects.all()
    import re, unicodedata
    from rapidfuzz import fuzz
    from django.db.models import Case, When, Value, IntegerField, Q
    
    if query:
        # --- Normalizer -----------------------------------------------------
        def normalize(text):
            text = str(text or "").lower()
            text = text.replace("&", "and").replace("–", "-").replace("—", "-").replace("\xa0", " ")
            text = unicodedata.normalize("NFKD", text)
            text = re.sub(r"[^a-z0-9]+", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
    
        query_norm = normalize(query)
        query_words = query_norm.split()
    
        # --- Scoring helper -------------------------------------------------
        def score_product(p):
            name = normalize(p.p_name)
            brand = normalize(p.brand_name)
            category = normalize(p.category.c_name)
            combined = f"{name} {brand} {category}"
    
            # 1️⃣ exact product name
            if name == query_norm:
                return 100
    
            # 2️⃣ exact brand name
            if brand == query_norm:
                return 99
    
            # 3️⃣ strong substring (brand/name/category contains full query)
            if query_norm in name or query_norm in brand or query_norm in category:
                return 90
    
            # 4️⃣ keyword overlap (any query word in name/brand/category)
            if any(w in combined for w in query_words):
                return 80
    
            # 5️⃣ fuzzy similarity (partial ratio)
            ratio = fuzz.partial_ratio(query_norm, combined)
            if ratio >= 60:
                return ratio  # will be between 60-89
    
            return 0  # not relevant
    
        # --- Score & collect -----------------------------------------------
        candidates = list(Product.objects.all())
        scored = [(score_product(p), p) for p in candidates if score_product(p) >= 60]
    
        # Sort strictly by score (descending)
        scored.sort(key=lambda sp: sp[0], reverse=True)
    
        # Extract ordered products
        matched_products = [p for _, p in scored]
    
        # --- Preserve order in DB (100/99 first) ----------------------------
        # Sort again in Python so 100% product names and 99% brand matches appear top
        matched_products = sorted(
            matched_products,
            key=lambda p: (
                0 if normalize(p.p_name) == query_norm else
                (1 if normalize(p.brand_name) == query_norm else 2)
            )
        )
    
        matched_ids = [p.p_id for p in matched_products]
    
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
        results = get_product_data1(Product.objects.all())






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
