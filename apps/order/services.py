from .repositories import OrderRepository, PaymentRepository


class OrderService:
    @staticmethod
    def place_order(user, customer_info, cart, selected_items):
        # Calculate the total amount based on selected items
        total_amount = sum(item.total_price for item in selected_items)

        # Create order and associate the selected items
        order = OrderRepository.create_order_snapshot(
            user, selected_items, total_amount
        )

        # Remove the selected items from the cart after order creation
        cart.items.filter(id__in=[item.id for item in selected_items]).delete()

        return order

    @staticmethod
    def calculate_total(order):
        return sum(item.total_price for item in order.items.all())


class PaymentService:
    @staticmethod
    def process_payment(order, method, amount, transaction_id=None):
        if amount != order.total_amount:
            raise ValueError("Payment amount does not match order total.")

        payment = PaymentRepository.create_payment(
            order, method, amount, transaction_id
        )
        payment = PaymentRepository.update_payment_status(
            payment, status="completed", transaction_id=transaction_id
        )
        OrderRepository.update_order_status(order, "pending")
        return payment
