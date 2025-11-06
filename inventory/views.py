from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from .models import Product, Category, Order, OrderItem
from accounts.models import CustomUser
from accounts.decorators import admin_required, staff_required, approved_user_required
from . import utils
import json

def home(request):
    # Get all active products with their categories
    products = Product.objects.filter(is_active=True).select_related('category')

    # Get categories sorted alphabetically and group products by category
    categories = Category.objects.filter(products__is_active=True).distinct().order_by('name')
    products_by_category = {}
    for category in categories:
        products_by_category[category] = products.filter(category=category)

    return render(request, 'inventory/home.html', {
        'products': products,
        'categories': categories,
        'products_by_category': products_by_category
    })

from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def update_stock(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 0))
            
            product = Product.objects.get(id=product_id)
            if product.stock_quantity >= quantity:
                product.stock_quantity -= quantity
                product.save()
                return JsonResponse({
                    'success': True,
                    'new_stock': product.stock_quantity,
                    'is_low_stock': product.is_low_stock
                })
            return JsonResponse({
                'success': False,
                'error': 'Not enough stock available'
            })
        except (Product.DoesNotExist, ValueError, json.JSONDecodeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid request'
            })
    return JsonResponse({'success': False, 'error': 'Invalid method'})

from django.db import transaction

@require_http_methods(["GET", "POST"])
def checkout(request):
    if request.method == 'GET':
        return JsonResponse({
            'success': False,
            'error': 'Please use POST method for checkout'
        })
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            customer_data = data.get('customerData', {})
            cart_items = data.get('cartItems', {})
            
            # Validate customer data
            required_fields = ['fullName', 'email', 'phone', 'deliveryAddress']
            if not all(field in customer_data and customer_data[field] for field in required_fields):
                return JsonResponse({
                    'success': False,
                    'error': 'Please fill in all required fields'
                })

            # Update user profile if requested
            if request.user.is_authenticated and customer_data.get('updateProfile'):
                User = get_user_model()
                user = User.objects.get(id=request.user.id)
                
                # Split full name into first_name and last_name
                full_name = customer_data['fullName'].split(maxsplit=1)
                user.first_name = full_name[0]
                user.last_name = full_name[1] if len(full_name) > 1 else ''
                
                user.phone_number = customer_data['phone']
                user.address = customer_data['deliveryAddress']
                # Don't update email as it might require verification
                user.save()
            
            # Validate cart is not empty
            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'error': 'Cart is empty'
                })

            # Start database transaction
            with transaction.atomic():
                # Check stock availability first
                for product_id, item in cart_items.items():
                    try:
                        product = Product.objects.get(id=product_id)
                        if product.stock_quantity < item['quantity']:
                            return JsonResponse({
                                'success': False,
                                'error': f'Insufficient stock for {product.name}'
                            })
                    except Product.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'error': f'Product with ID {product_id} not found'
                        })

                # Calculate total amount
                total_amount = sum(float(item['price']) * item['quantity'] for item in cart_items.values())
                
                # Create the order
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=customer_data['fullName'],
                    address=customer_data['deliveryAddress'],
                    phone=customer_data['phone'],
                    email=customer_data['email'],
                    total_amount=total_amount,
                    status='pending'
                )

                # Create order items
                for product_id, item in cart_items.items():
                    product = Product.objects.get(id=product_id)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price']
                    )

                # Update stock quantities
                for product_id, item in cart_items.items():
                    product = Product.objects.get(id=product_id)
                    item_quantity = item.get('quantity', 0)
                    if item_quantity > 0:
                        product.stock_quantity -= item_quantity
                        product.save()
                        
                        # Send low stock alert if needed
                        if product.is_low_stock:
                            transaction.on_commit(lambda p=product: utils.send_stock_alert(p))

                order_summary = {
                    'customer': customer_data,
                    'items': cart_items,
                    'total': total_amount,
                    'order_id': order.id
                }
                for product_id, item in cart_items.items():
                    product = Product.objects.get(id=product_id)
                    item_quantity = item.get('quantity', 0)
                    if item_quantity > 0:
                        product.stock_quantity -= item_quantity
                        product.save()
                        
                        # Send low stock alert if needed
                        if product.is_low_stock:
                            transaction.on_commit(lambda p=product: utils.send_stock_alert(p))

                # Queue confirmation email to be sent after successful transaction
                # Queue confirmation email to be sent after successful transaction
                transaction.on_commit(lambda: utils.send_order_confirmation({
                    'customerData': customer_data,
                    'cartItems': cart_items,
                    'orderId': order.id
                }))

            return JsonResponse({
                'success': True,
                'message': 'Order placed successfully!',
                'orderSummary': order_summary
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid request data'
            })
            
    return JsonResponse({
        'success': False,
        'error': 'Invalid method'
    })

@admin_required
def admin_dashboard(request):
    context = {
        'total_users': CustomUser.objects.count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.filter(status='delivered').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'recent_orders': Order.objects.order_by('-created_at')[:5],
        'low_stock_products': Product.objects.filter(stock_quantity__lt=10)
    }
    return render(request, 'inventory/admin_dashboard.html', context)

@staff_required
def staff_inventory(request):
    if request.method == 'POST':
        try:
            data = request.POST
            image = request.FILES.get('image')
            
            product = Product.objects.create(
                name=data['name'],
                category_id=data['category'],
                price=data['price'],
                stock_quantity=data['stock_quantity'],
                image=image
            )
            return JsonResponse({'success': True, 'product_id': product.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    context = {
        'products': Product.objects.all().order_by('category', 'name'),
        'categories': Category.objects.all()
    }
    return render(request, 'inventory/staff_inventory.html', context)

@require_http_methods(["DELETE"])
@staff_required
def delete_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        return JsonResponse({'success': True})
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@approved_user_required
def customer_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Add status colors for badges
    for order in orders:
        if order.status == 'pending':
            order.status_color = 'warning'
        elif order.status == 'processing':
            order.status_color = 'info'
        elif order.status == 'shipped':
            order.status_color = 'primary'
        elif order.status == 'delivered':
            order.status_color = 'success'
        elif order.status == 'cancelled':
            order.status_color = 'danger'
    
    return render(request, 'inventory/customer_orders.html', {'orders': orders})
