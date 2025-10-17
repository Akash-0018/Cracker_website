from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{Decimal(amount):.2f}"

def send_order_confirmation(order_data):
    """Send order confirmation email to customer"""
    try:
        subject = 'Order Confirmation - Kannan Crackers'
        customer_data = order_data.get('customerData', {})
        
        if not all(key in customer_data for key in ['fullName', 'email', 'phone', 'deliveryAddress']):
            raise ValueError("Missing required customer data")
            
        # Calculate order total and format cart items
        cart_items = order_data['cartItems']
        items_html = ""
        order_total = Decimal('0.00')
        
        for item_id, item in cart_items.items():
            item_price = Decimal(str(item['price']))
            item_quantity = Decimal(str(item['quantity']))
            item_total = item_price * item_quantity
            order_total += item_total
            items_html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item_quantity}</td>
                    <td>{format_currency(item_price)}</td>
                    <td>{format_currency(item_total)}</td>
                </tr>
            """
            
        # Prepare email context
        context = {
            'customer_name': order_data['customerData']['fullName'],
            'order_total': format_currency(order_total),
            'items_html': items_html,
            'delivery_address': order_data['customerData']['deliveryAddress'],
            'phone': order_data['customerData']['phone'],
            'email': order_data['customerData']['email'],
            'cart_items': cart_items.values()
        }

        # Render email templates
        html_message = render_to_string('inventory/email/order_confirmation.html', context)
        plain_message = render_to_string('inventory/email/order_confirmation.txt', context)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order_data['customerData']['email']],
            html_message=html_message,
            fail_silently=False
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send order confirmation email: {str(e)}")
        return False

    # Prepare email context
    context = {
        'customer_name': order_data['customerData']['fullName'],
        'order_total': format_currency(order_total),
        'items_html': items_html,
        'delivery_address': order_data['customerData']['deliveryAddress'],
        'phone': order_data['customerData']['phone'],
        'email': order_data['customerData']['email']
    }

    # Render email templates
    html_message = render_to_string('inventory/email/order_confirmation.html', context)
    plain_message = render_to_string('inventory/email/order_confirmation.txt', context)

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order_data['customerData']['email']],
        html_message=html_message
    )

def send_stock_alert(product):
    """Send low stock alert to admin"""
    subject = f'Low Stock Alert - {product.name}'
    
    context = {
        'product_name': product.name,
        'current_stock': product.stock_quantity,
        'category': product.category.name
    }

    # Render email templates
    html_message = render_to_string('inventory/email/stock_alert.html', context)
    plain_message = render_to_string('inventory/email/stock_alert.txt', context)

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],  # Send to admin email
        html_message=html_message
    )