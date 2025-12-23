"""
URL configuration for billingManagementSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from billing.views import *
from orderFood.views import *
from orderFood import views

urlpatterns = [
    path('', auth, name='home'),  # Redirect root to auth view (login/signup)
    path('auth/', auth, name='auth'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),  # Add the logout path
    path('orderCreate/', orderCreate, name='orderCreate'),  # Add the logout path
    path('orderStoreDetails/', orderStoreDetails, name='orderStoreDetails'),  
    path('orderDetailIndex/', orderDetailIndex, name='orderDetailIndex'),  
    path('oorderDetailsView/', views.orderDetailsView, name='orderDetailsView'),  # 👈 use 'order_details' here
    path('editOrderCreate/', views.editOrderCreate, name='editOrderCreate'),  # 👈 use 'order_details' here
    path('order/update/', orderUpdateDetails, name='orderUpdateDetails'),
    path('get_menu_price/', get_menu_price, name='get_menu_price'),
    path('order/item/delete/', views.delete_order_item, name='delete_order_item'),

]



