from django.urls import path, include
from .views import (
    StripePaymentAndOrderView,
    OrderList,
    RetrieveOrder,
    OrderUpdateView,
    DeliveryNoteList,
    AllInvoice,
    DeliveryNoteRetrieveView,
    InvoiceRetrieveView,
    OrderGraphDataView,
    ReviewListCreateAPIView,
    OrderProductSummaryAPIView,
    OfflinePayment, ReviewAPIView, CompletedOrderListAPIView,
)
from .graph import (
    OrderOverviewGraphDataView,
    SalesByProductAPIView,
    SalesByCustomersView,
    TotalSellAndTotalDelivery,
)

urlpatterns = [
    path("", OrderList.as_view(), name="order-list"),
    path("<int:pk>/", RetrieveOrder.as_view(), name="order-detail"),
    path("payment/stripe/", StripePaymentAndOrderView.as_view(), name="stripe"),
    path("payment/offline/", OfflinePayment.as_view(), name="offline-payment"),
    path("<int:pk>/update/", OrderUpdateView.as_view(), name="order-update"),
    path("delivery-note/", DeliveryNoteList.as_view(), name="delivery-note-list"),
    path(
        "delivery-note/<int:pk>/",
        DeliveryNoteRetrieveView.as_view(),
        name="delivery-note-detail",
    ),
    path("invoice/", AllInvoice.as_view(), name="invoice-list"),
    path("invoice/<int:pk>/", InvoiceRetrieveView.as_view(), name="invoice-detail"),
    path("graph-data/delivery/", OrderGraphDataView.as_view(), name="order-graph-data"),
    # review management
    path("review/", ReviewListCreateAPIView.as_view(), name="review-management"),
    
    path('completed/', CompletedOrderListAPIView.as_view(), name='completed-orders'),
    
     path('review/<str:order_number>/', ReviewAPIView.as_view(), name='order-reviews-api'),
    # order product summary
    path(
        "order-product-summary/",
        OrderProductSummaryAPIView.as_view(),
        name="order-product-summary",
    ),
    # order overview graph data
    path(
        "order-overview-graph-data/",
        OrderOverviewGraphDataView.as_view(),
        name="order-overview-graph-data",
    ),
    # sales by product
    path("sales-by-product/", SalesByProductAPIView.as_view(), name="sales-by-product"),
    # sales by customers
    path(
        "sales-by-customers/", SalesByCustomersView.as_view(), name="sales-by-customers"
    ),
    # total sell and total delivery
    path(
        "total-sell-and-delivery/",
        TotalSellAndTotalDelivery.as_view(),
        name="total-sell-and-delivery",
    ),
]
