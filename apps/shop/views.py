from .models import Products
from .serializers import ProductsSerializer, ProductListsSerializer
from ..core.crud import DynamicModelViewSet
from ..core.pagination import CustomPagination
from ..core.permissions import IsAdminRole
from apps.core.getList import BaseListAPIView
from apps.core.getDetails import BaseRetrieveAPIView


class ProductsViewSet(DynamicModelViewSet):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminRole]

    def __init__(self, *args, **kwargs):
        kwargs["model"] = Products
        kwargs["serializer_class"] = ProductsSerializer
        kwargs["item_name"] = "Products"
        super().__init__(*args, **kwargs)


class ProductListView(BaseListAPIView):
    queryset = Products.objects.all().order_by("-id")
    serializer_class = ProductListsSerializer
    pagination_class = CustomPagination


class ProductRetrieveView(BaseRetrieveAPIView):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer
