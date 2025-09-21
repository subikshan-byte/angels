from django.urls import path
from . import views
from . import views2
urlpatterns = [
    path('home',views.home,name='home'),
    path('<slug:p>',views.product_detail,name='product'),
    path('<str:c>',views2.category,name="category")
]
