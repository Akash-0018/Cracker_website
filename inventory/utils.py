from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{Decimal(amount):.2f}"

import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def send_order_confirmation(order_data):
    """Send order confirmation email to customer"""
    try:
        subject = f'Order Confirmation - Kannan Crackers (Order #{order_data.get("orderId", "N/A")})'            
        customer_data = order_data.get('customerData', {})
        
        required_fields = ['fullName', 'email', 'phone', 'deliveryAddress']
        missing_fields = [field for field in required_fields if not customer_data.get(field)]
        
        if missing_fields:
            raise ValidationError(f"Missing required customer data: {', '.join(missing_fields)}")
        
        # Validate email format
        if '@' not in customer_data['email']:
            raise ValidationError("Invalid email format")
        
        # Validate phone number (assuming 10 digits)
        if not customer_data['phone'].isdigit() or len(customer_data['phone']) != 10:
            raise ValidationError("Invalid phone number format")
            
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
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order_data['customerData']['email']],
                html_message=html_message,
                fail_silently=False
            )
            logger.info(f"Order confirmation email sent successfully to {order_data['customerData']['email']} for order #{order_data.get('orderId', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email to {order_data['customerData']['email']}: {str(e)}")
            # Re-raise the exception to be handled by the view
            raise
            
    except ValidationError as e:
        logger.error(f"Validation error in order confirmation email: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error in order confirmation email: {str(e)}")
        raise



def send_stock_alert(product):
    """Send low stock alert to admin"""
    subject = f'Low Stock Alert - {product.name}'
    
    context = {
        'product': product
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