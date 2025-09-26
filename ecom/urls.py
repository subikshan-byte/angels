from django.urls import path
from . import views
from . import views3,views2
urlpatterns = [
    path('home',views.home,name='home'),
    path('search', views3.search, name='search'),
    path('<slug:p>',views.product_detail,name='product'),
    path('shop',views2.shop,name="shop")
]
