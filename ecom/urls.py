from django.urls import path,include
from . import views
from . import views3,views2,views4,views5,views6,views7,views8
urlpatterns = [
    path('home',views.home,name='home'),
    path('<str:s>/search', views3.search, name='search'),
     path('login',views4.login_view,name="login"),
     path("logout/", views4.logout_view, name="logout"),
     path('signup/', views4.signup_view, name='signup'),
     path('myaccount',views5.account_detail,name="myaccount"),
     path("cart",views5.cart,name="cart"),
     path("addcart/<slug:product_id>",views5.add_to_cart,name="add to cart"),
     path('edit',views5.edit_profile,name="edit"),
     path('accounts/', include('allauth.urls')),
    path('product/<slug:p>',views.product_detail,name='product'), 
    path('cart/remove/<int:item_id>/', views5.remove_from_cart, name='remove_from_cart'),
    path('cart1/remove1/<int:item_id>/', views5.remove_from_cart1, name='remove_from_cart1'),
    path('buy/<slug:slug>/', views6.buy_now, name='buy_now'),
path('payment/success/', views6.payment_success, name='payment_success'),
path('cart/update/<int:cart_item_id>/', views6.update_cart_quantity, name='update_cart_quantity'),
path('checkout/cart/', views7.cart_checkout, name='cart_checkout'),

    # Payment success for cart
    path('payment/success-cart/', views7.payment_success_cart, name='cart_payment_success'),
    path("about",views8.about,name="about"),
    path("contact",views8.contact,name="contact")
]


