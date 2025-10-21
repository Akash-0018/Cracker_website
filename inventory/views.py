from django.shortcuts import render
from django.http import JsonResponse
from .models import Product
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from . import utils
import json

def home(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    return render(request, 'inventory/home.html', {'products': products})

@csrf_exempt
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

@csrf_exempt
def checkout(request):
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
            
            # Process order (you can save to database here)
            order_summary = {
                'customer': customer_data,
                'items': cart_items,
                'total': sum(float(item['price']) * item['quantity'] for item in cart_items.values())
            }

            # Update stock quantities
            for product_id, item in cart_items.items():
                try:
                    product = Product.objects.get(id=product_id)
                    item_quantity = item.get('quantity', 0)
                    if item_quantity > 0:
                        product.stock_quantity -= item_quantity
                        product.save()
                        
                        # Send low stock alert if needed
                        if product.is_low_stock:
                            utils.send_stock_alert(product)
                except Product.DoesNotExist:
                    continue

            # Send order confirmation email
            try:
                utils.send_order_confirmation({
                    'customerData': customer_data,
                    'cartItems': cart_items
                })
            except Exception as e:
                print(f"Failed to send email: {str(e)}")  # Log the error but don't fail the order

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
