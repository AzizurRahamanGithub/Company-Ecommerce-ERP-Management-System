from .models import Cart, CartItem

class CartRepository:
    """Handle all DB operations related to Cart"""

    @staticmethod
    def get_cart(user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @staticmethod
    def get_cart_items(cart):
        return CartItem.objects.filter(cart=cart)

    @staticmethod
    def add_item(cart, product, quantity=1):
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
        return item

    @staticmethod
    def remove_item(cart, product):
        try:
            item = CartItem.objects.get(cart=cart, product=product)
            item.delete()
            return True
        except CartItem.DoesNotExist:
            return False

    @staticmethod
    def clear_cart(cart):
        cart.items.all().delete()
        return True

    @staticmethod
    def update_item_quantity(cart, product, quantity):
        try:
            item = CartItem.objects.get(cart=cart, product=product)
            item.quantity = quantity
            item.save()
            return item
        except CartItem.DoesNotExist:
            return None