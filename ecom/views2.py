from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404
from .models import Product, ProductImage,Size
def category(request,c):
    return HttpResponse(c)