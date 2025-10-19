from django.urls import path,include
from . import views
from . import views3,views2,views4,views5,views6,views7,views8,forgetpass,check
urlpatterns = [
    path('',views.home,name='home'),
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
    path('verify-order-otp/', views6.verify_order_otp, name='verify_order_otp'),
 
path('cart/update/<int:cart_item_id>/', views6.update_cart_quantity, name='update_cart_quantity'),
path('checkout/cart/', views7.cart_checkout, name='cart_checkout'),
    path("send-checkout-otp/", views6.send_checkout_otp, name="send_checkout_otp"),
    path('create-razorpay-order/', views6.create_razorpay_order, name='create_razorpay_order'),
path('place-cod-order/', views6.place_cod_order, name='place_cod_order'),
path('apply-coupon/', views6.apply_coupon, name='apply_coupon'),



    # Payment success for cart
    path('payment/success-cart/', views7.payment_success_cart, name='cart_payment_success'),
    path("about",views8.about,name="about"),
    path("contact",views8.contact,name="contact"),
    path("privacy",views8.privacy,name="privacy"),
      path('forgot-password/', forgetpass.forgot_password, name='forgot_password'),
    path('verify-otp/', forgetpass.verify_otp, name='verify_otp'),
    path('reset-password/', forgetpass.reset_password, name='reset_password'),
    path('order-check/', check.order_check, name='order_check'),
]


