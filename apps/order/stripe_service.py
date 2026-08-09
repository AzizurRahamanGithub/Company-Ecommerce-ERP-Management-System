import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def ensure_customer_for_user(user):
    customer_id = user.stripe_customer_id

    if customer_id:
        # ✅ Stale ID হলে reset করো
        try:
            stripe.Customer.retrieve(customer_id)
        except stripe.error.InvalidRequestError:
            user.stripe_customer_id = None
            user.save(update_fields=["stripe_customer_id"])
            customer_id = None

    if not customer_id:
        customer_id = create_stripe_customer(user)

    return customer_id


def create_stripe_customer(user):
    # ✅ user.name নেই — সঠিক field থেকে নাও
    try:
        name = user.customer_account.business_name
    except Exception:
        name = user.full_name or user.email.split("@")[0]

    stripe_customer = stripe.Customer.create(
        email=user.email,
        name=name,
    )
    user.stripe_customer_id = stripe_customer.id
    user.save(update_fields=["stripe_customer_id"])

    return stripe_customer.id


# ---- বাকি সব same থাকবে ----
def ensure_pm_attached_to_customer(payment_method_id, customer_id):
    try:
        pm = stripe.PaymentMethod.retrieve(payment_method_id)
    except stripe.error.InvalidRequestError:
        raise Exception(
            f"Payment method '{payment_method_id}' does not exist in Stripe. "
            f"This usually means a test/live key mismatch, or the PM ID is stale."
        )

    if pm.customer == customer_id:
        return

    if pm.customer and pm.customer != customer_id:
        raise Exception(
            f"Payment method '{payment_method_id}' is already attached to a different "
            f"customer ({pm.customer}). Create a new payment method for this customer."
        )

    try:
        stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
        )
    except stripe.error.StripeError as e:
        raise Exception(f"Failed to attach payment method: {str(e)}")