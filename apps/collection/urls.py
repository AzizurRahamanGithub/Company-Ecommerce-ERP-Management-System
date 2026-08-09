from django.urls import path
from .views import (
    MilkCollectionListCreateAPIView, MilkCollectionDetailAPIView, AllSuppliersAPIView,
    AllMilkCollectionHistoryAPIView,WeeklyMilkCollectionHistoryAPIView, NextDayMilkCollectionAPIView, YieldCalculationListCreateAPIView, YieldAlertAPIView
  , WeeklyCollectionCountAPIView, TodayMilkCollectionAPIView, MilkPurchaseFromSuppliers, MilkWualityBySupplier, MilkQualityFromSuplier, SCCVisualizationAPIView, MilkQualityVisualizationAPIView, SupplierListAPIView
)

from apps.production.views import YieldVisualizationAPIView

urlpatterns = [
    # Milk Collection History API
    path('milk-collections/history/', AllMilkCollectionHistoryAPIView.as_view(), name='all_milk_collections_history'),
    path('milk-collections/weekly/', WeeklyMilkCollectionHistoryAPIView.as_view(), name='weekly_milk_collections'),
    path('milk-collections/today/', TodayMilkCollectionAPIView.as_view(), name='today-milk-collections'),
    path('milk-collections/next-day/', NextDayMilkCollectionAPIView.as_view(), name='next-day-milk-collections'),
    
    path('milk-collections/supplier-count/', WeeklyCollectionCountAPIView.as_view(), name='weekly-collection-count'),
    
    path('yield_calculations/', YieldCalculationListCreateAPIView.as_view(), name='yield-calculation-list-create'),
    path('alert/yield_calculations/', YieldAlertAPIView.as_view(), name='yield-alert'),
    path('yield/visualization/', YieldVisualizationAPIView.as_view(), name='yield-visualization'),
    
    path("suppliers/", AllSuppliersAPIView.as_view(), name="supplier-by-username"),
    # Milk Collections
    path('milk-collections/', MilkCollectionListCreateAPIView.as_view(), name='milkcollection-list-create'),
    path('milk-collections/<int:pk>/', MilkCollectionDetailAPIView.as_view(), name='milkcollection-detail'),
    
    
    path('milk-purchase-from-suppliers/', MilkPurchaseFromSuppliers.as_view(), name='milkcollection-detail'),
    
    path('milk-quality-from-suppliers/', MilkWualityBySupplier.as_view(), name='milk-quality-from-suppliers'),
    
    path('milk-ph-from-suppliers/', MilkQualityFromSuplier.as_view(), name='milk-ph-from-suppliers'),
    path('scc-visualization/', SCCVisualizationAPIView.as_view(), name='scc-visualization'),
    path('milk-quality-visualization/', MilkQualityVisualizationAPIView.as_view(), name='milk-quality'),
    path('active-supplier/', SupplierListAPIView.as_view(), name='milk-quality'),
    
]
