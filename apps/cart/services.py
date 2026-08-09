from django.shortcuts import get_object_or_404
from apps.shop.models import Products
from .repositories import CartRepository
from .models import Cart

class CartService:
    """Business logic for cart operations"""

    @staticmethod
    def get_user_cart(user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart
    
    @staticmethod
    def add_to_cart(user, product_id, quantity=1):
        cart = CartRepository.get_cart(user)
        product = get_object_or_404(Products, id=product_id)  
        item = CartRepository.add_item(cart, product, quantity)
        CartService._update_shipping(cart)
        return item

    @staticmethod
    def remove_from_cart(user, product_id):
        cart = CartRepository.get_cart(user)
        product = get_object_or_404(Products, id=product_id)
        CartRepository.remove_item(cart, product)
        CartService._update_shipping(cart)
        return True

    @staticmethod
    def clear_cart(user):
        cart = CartRepository.get_cart(user)
        CartRepository.clear_cart(cart)
        CartService._update_shipping(cart)
        return True

    @staticmethod
    def _update_shipping(cart):
        """Apply shipping logic based on subtotal"""
        subtotal = cart.subtotal
        if subtotal == 0:
            cart.shipping_cost = 0
        elif subtotal < 1000:
            cart.shipping_cost = 0
        else:
            cart.shipping_cost = 0
        cart.save()

    @staticmethod
    def update_item_quantity(user, product_id, quantity):
        cart = CartRepository.get_cart(user)
        product = get_object_or_404(Products, id=product_id)
        return CartRepository.update_item_quantity(cart, product, quantity)