document.addEventListener('DOMContentLoaded', function() {
    const productGrid = document.getElementById('product-grid');
    const cartTotalElements = document.querySelectorAll('#cart-total');
    const cartItemsCount = document.querySelector('.cart-items-count');
    const cartItemsContainer = document.getElementById('cartItems');
    const modalSubtotal = document.getElementById('modalSubtotal');
    const checkoutForm = document.getElementById('checkoutForm');
    const checkoutButton = document.getElementById('proceedToCheckout');
    let totalCartAmount = 0;
    let cartItems = {};

    // Function to update all cart total displays
    function updateAllCartTotals(amount) {
        cartTotalElements.forEach(element => {
            element.textContent = amount.toFixed(2);
        });
        modalSubtotal.textContent = amount.toFixed(2);
    }

    // Function to update cart items count
    function updateCartCount() {
        const itemCount = Object.values(cartItems).reduce((sum, item) => sum + item.quantity, 0);
        cartItemsCount.textContent = `(${itemCount} items)`;
    }

    // Function to render cart items in modal
    function renderCartItems() {
        cartItemsContainer.innerHTML = '';
        Object.entries(cartItems).forEach(([id, item]) => {
            const itemTotal = item.price * item.quantity;
            const itemHtml = `
                <div class="cart-item" data-id="${id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-1">${item.name}</h5>
                            <p class="mb-0">Quantity: ${item.quantity}</p>
                        </div>
                        <div class="text-end">
                            <div class="cart-item-price">₹${itemTotal.toFixed(2)}</div>
                            <button class="btn btn-sm btn-danger remove-item">Remove</button>
                        </div>
                    </div>
                </div>
            `;
            cartItemsContainer.insertAdjacentHTML('beforeend', itemHtml);
        });
    }

    // Update individual item total
    function updateItemTotal(card) {
        const quantity = parseInt(card.querySelector('.quantity-input').value);
        const price = parseFloat(card.querySelector('.price').innerText.replace('₹', ''));
        const totalPrice = (quantity * price).toFixed(2);
        card.querySelector('.total-price').innerText = totalPrice;
        updateCartTotal();
    }

    // Update cart total
    function updateCartTotal() {
        totalCartAmount = Object.values(cartItems).reduce((sum, item) => {
            return sum + (item.price * item.quantity);
        }, 0);
        updateAllCartTotals(totalCartAmount);
    }

    // Handle quantity changes
    productGrid.addEventListener('click', function(e) {
        if (e.target.classList.contains('decrease-qty') || e.target.classList.contains('increase-qty')) {
            const card = e.target.closest('.card');
            const input = card.querySelector('.quantity-input');
            const currentValue = parseInt(input.value);
            const maxStock = parseInt(input.max);

            if (e.target.classList.contains('decrease-qty')) {
                if (currentValue > 1) {
                    input.value = currentValue - 1;
                }
            } else {
                if (currentValue < maxStock) {
                    input.value = currentValue + 1;
                }
            }
            updateItemTotal(card);
        }
    });

    // Handle manual quantity input
    productGrid.addEventListener('input', function(e) {
        if (e.target.classList.contains('quantity-input')) {
            const card = e.target.closest('.card');
            const maxStock = parseInt(e.target.max);
            let value = parseInt(e.target.value) || 1;
            
            // Ensure quantity is within valid range
            value = Math.max(1, Math.min(value, maxStock));
            e.target.value = value;
            
            updateItemTotal(card);
        }
    });

    // Handle add to cart
    productGrid.addEventListener('click', async function(e) {
        if (e.target.classList.contains('add-to-cart') || e.target.parentElement.classList.contains('add-to-cart')) {
            const card = e.target.closest('.card');
            const productId = card.dataset.productId;
            const quantity = parseInt(card.querySelector('.quantity-input').value);
            const stockElement = card.querySelector('.stock-quantity');
            const productName = card.querySelector('.card-title').textContent;
            const currentStock = parseInt(stockElement.innerText);

            try {
                const response = await fetch('/inventory/update-stock/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        product_id: productId,
                        quantity: quantity
                    })
                });

                const data = await response.json();
                
                if (data.success) {
                    // Update stock display
                    stockElement.innerText = data.new_stock;
                    
                    // Update max quantity
                    const quantityInput = card.querySelector('.quantity-input');
                    quantityInput.max = data.new_stock;
                    
                    // Disable controls if no stock
                    if (data.new_stock === 0) {
                        quantityInput.disabled = true;
                        e.target.disabled = true;
                    }
                    
                    // Update low stock styling
                    if (data.is_low_stock) {
                        card.classList.add('low-stock');
                    }
                    
                    // Reset quantity input
                    quantityInput.value = 1;
                    updateItemTotal(card);
                    
                    // Update cart items
                    if (!cartItems[productId]) {
                        cartItems[productId] = {
                            name: productName,
                            quantity: 0,
                            price: parseFloat(card.querySelector('.price').innerText.replace('₹', ''))
                        };
                    }
                    cartItems[productId].quantity += quantity;
                    
                    // Update displays
                    updateCartTotal();
                    updateCartCount();
                    renderCartItems();

                    // Show success toast
                    const message = `Added ${quantity} ${productName} to cart`;
                    alert(message);
                } else {
                    alert(data.error || 'Failed to add items to cart');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to update cart. Please try again.');
            }
        }
    });

    // Handle remove item from cart
    cartItemsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-item')) {
            const cartItem = e.target.closest('.cart-item');
            const itemId = cartItem.dataset.id;
            delete cartItems[itemId];
            updateCartTotal();
            updateCartCount();
            renderCartItems();
        }
    });

    // Handle checkout form submission
    checkoutButton.addEventListener('click', async function() {
        if (!checkoutForm.checkValidity()) {
            checkoutForm.classList.add('was-validated');
            return;
        }

        const formData = new FormData(checkoutForm);
        const customerData = {
            fullName: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            deliveryAddress: document.getElementById('deliveryAddress').value
        };

        try {
            const response = await fetch('/inventory/checkout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customerData: customerData,
                    cartItems: cartItems
                })
            });

            const data = await response.json();
            
            if (data.success) {
                // Clear cart
                cartItems = {};
                updateCartTotal();
                updateCartCount();
                renderCartItems();

                // Show success message
                const modalBody = document.querySelector('.modal-body');
                modalBody.innerHTML = `
                    <div class="checkout-success">
                        <i class="bi bi-check-circle"></i>
                        <h4>Order Placed Successfully!</h4>
                        <p>Thank you for your order. We will contact you shortly.</p>
                        <p>Order Total: ₹${data.orderSummary.total.toFixed(2)}</p>
                    </div>
                `;
                
                // Change modal footer
                const modalFooter = document.querySelector('.modal-footer');
                modalFooter.innerHTML = `
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Continue Shopping</button>
                `;
            } else {
                alert(data.error || 'Failed to place order. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to place order. Please try again.');
        }
    });

    // Initialize item totals
    document.querySelectorAll('.card').forEach(updateItemTotal);
});