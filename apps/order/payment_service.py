from django.conf import settings
import stripe
from .repositories import OrderRepository, PaymentRepository
from .stripe_service import ensure_pm_attached_to_customer, ensure_customer_for_user
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    @staticmethod
    def create_payment(amount, payment_method_id, user):
        """Handle Stripe payment intent"""
        try:
            # Create or fetch the customer (assumed function)
            customer_id = ensure_customer_for_user(user)

            # Attach the payment method to the customer (assumed function)
            ensure_pm_attached_to_customer(payment_method_id, customer_id)

            # Create the payment intent with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=int(Decimal(amount) * 100),  # Convert to cents
                currency="usd",
                confirm=True,
                customer=customer_id,
                payment_method=payment_method_id,
                description=f"Booking payment for {user.first_name} {user.last_name}",
                metadata={"user_id": str(user.id), "email": user.email},
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            return payment_intent
        except stripe.error.StripeError as e:
            # Surface a user-facing message if available
            raise Exception(getattr(e, "user_message", str(e)))


class CashOnDeliveryPaymentService:
    @staticmethod
    def process_payment(order, amount):
        """Handles Cash on Delivery payment."""
        payment = PaymentRepository.create_payment(
            order, "cash", amount, status="completed"
        )
        OrderRepository.update_order_status(order, "pending")
        return payment


class MMGPaymentService:
    @staticmethod
    def process_payment(order, amount, phone_number):
        """Handles Mobile Money (MMG) payment."""
        payment = PaymentRepository.create_payment(
            order, "mmg", amount, phone_number, "completed"
        )
        OrderRepository.update_order_status(order, "pending")
        return payment
