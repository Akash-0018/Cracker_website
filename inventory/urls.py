from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.home, name='home'),
    path('update-stock/', views.update_stock, name='update_stock'),
    path('checkout/', views.checkout, name='checkout'),
]