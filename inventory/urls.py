from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.home, name='home'),
    path('update-stock/', views.update_stock, name='update_stock'),
    path('checkout/', views.checkout, name='checkout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/inventory/', views.staff_inventory, name='staff_inventory'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('orders/', views.customer_orders, name='customer_orders'),
]