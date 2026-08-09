from .serializers import CartSerializer
from .services import CartService
from rest_framework.views import APIView
from apps.core.response import success_response, failure_response
from rest_framework.permissions import IsAuthenticated


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = CartService.get_user_cart(request.user)
        serializer = CartSerializer(cart)
        return success_response("Cart retrieved successfully", serializer.data)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
        CartService.add_to_cart(request.user, product_id, quantity)
        cart = CartService.get_user_cart(request.user)
        serializer = CartSerializer(cart)
        return success_response("Product added to cart successfully", serializer.data)


class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        removed = CartService.remove_from_cart(request.user, product_id)
        if removed:
            cart = CartService.get_user_cart(request.user)
            serializer = CartSerializer(cart)
            return success_response("Product removed successfully", serializer.data)
        return failure_response("Product not found in cart")


class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        CartService.clear_cart(request.user)
        cart = CartService.get_user_cart(request.user)
        serializer = CartSerializer(cart)
        return success_response("Cart cleared successfully", serializer.data)


class CartItemQuantityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        quantity = int(request.data.get("quantity", 1))
        item = CartService.update_item_quantity(request.user, product_id, quantity)
        if item:
            cart = CartService.get_user_cart(request.user)
            serializer = CartSerializer(cart)
            return success_response(
                "Product quantity updated successfully", serializer.data
            )
        return failure_response("Product not found in cart")
    


class UpdateCartProductQuantityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        action_type = request.data.get("type")  

        # Get user's cart
        cart = CartService.get_user_cart(request.user)
        item = cart.items.filter(product_id=product_id).first()

        if not item:
            return failure_response("Product not found in cart")

        # Update quantity based on type
        if action_type == "increment":
            item.quantity += 1
        elif action_type == "decrement" and item.quantity > 1:
            item.quantity -= 1
        else:
            return failure_response("Invalid action or minimum quantity reached")

        item.save()

        # Serialize updated cart
        serializer = CartSerializer(cart)
        return success_response("Product quantity updated successfully", serializer.data)
