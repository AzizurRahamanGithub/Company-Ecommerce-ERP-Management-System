from .models import Order, OrderItem, PaymentHistory
from apps.shop.models import Products as Product
import time


class OrderRepository:
    @staticmethod
    def create_order_snapshot(user, items, total_amount,delivery_date,delivery_address,delivery_area,payment_method="stripe"):
        order_items = []

        # Loop through the selected items and fetch the product details
        for item in items:
            if isinstance(item, dict) and 'product' in item and 'quantity' in item:
                # Fetch the product from the database using the product ID
                try:
                    product = Product.objects.get(id=item['product'])  
                except Product.DoesNotExist:
                    raise Exception(f"Product with ID {item['product']} not found.")

                quantity = item['quantity']
                
                # Now create the order items
                order_items.append({
                    "product_id": product.id,
                    "quantity": quantity,
                    "category": product.category,
                    "product_name": product.name,
                    "price": float(product.price),  # Convert Decimal to float
                    "total_price": float(product.price * quantity),  # Convert Decimal to float
                    "product_image": product.images,
                })

        customer_info = {
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "address": user.address,
            "customer_code": user.customer_code,
            "profile_image": user.image
        }

        # Create the order with total_amount converted to float
        order = Order.objects.create(
            order_number=f"ORD{user.id}{int(time.time())}",
            user=user,
            customer_info=customer_info,
            order_items=order_items,
            total_amount=float(total_amount),  # Convert Decimal to float
            delivery_date=delivery_date,
            delivery_address=delivery_address,
            delivery_area=delivery_area,
            payment_method=payment_method
        )
        print("order created", order)
        print("delvie area", delivery_area)
        
        # Create OrderItem entries for each product in the order
        for item in items:
            if isinstance(item, dict) and 'product' in item and 'quantity' in item:
                product = Product.objects.get(id=item['product'])  # Fetch the product again
                quantity = item['quantity']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=float(product.price),  # Convert Decimal to float
                )

        return order

    @staticmethod
    def update_order_status(order, status):
        order.order_status = status
        order.save()
        return order

    @staticmethod
    def get_order_by_id(order_id):
        return (
            Order.objects.prefetch_related("items", "payments")
            .filter(id=order_id)
            .first()
        )


class PaymentRepository:
    @staticmethod
    def create_payment(order, method, amount, transaction_id=None, status="pending"):
        payment = PaymentHistory.objects.create(
            order=order,
            payment_method=method,
            amount=amount,
            transaction_id=transaction_id,
            payment_status=status,
        )
        return payment

    @staticmethod
    def update_payment_status(payment, status, transaction_id=None):
        payment.payment_status = status
        if transaction_id:
            payment.transaction_id = transaction_id
        payment.save()
        return payment
