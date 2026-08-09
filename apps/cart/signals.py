from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CartItem

@receiver(post_save, sender=CartItem)
def notify_cart_item_added(sender, instance, created, **kwargs):
    if created:
        print(f"Notification: {instance.quantity} x {instance.product.name} added to cart for {instance.cart.user.username}")
