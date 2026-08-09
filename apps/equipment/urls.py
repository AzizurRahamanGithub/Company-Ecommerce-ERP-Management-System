from django.urls import path
from .views import (
    EquipmentCleaningListCreateAPIView,
    EquipmentCleaningDetailAPIView,
    AreaCleaningListCreateAPIView,
    AreaCleaningDetailAPIView,
    AllSenitizersAPIView, CleaningKPIAPIView, CleaningOverallScoreAPIView
)

urlpatterns = [
    # Equipment Cleaning URLs
    path('equipment-cleaning/', EquipmentCleaningListCreateAPIView.as_view(), name='equipment-cleaning-list-create'),
    path('equipment-cleaning/<int:pk>/', EquipmentCleaningDetailAPIView.as_view(), name='equipment-cleaning-detail'),

    # Area Cleaning URLs
    path('area-cleaning/', AreaCleaningListCreateAPIView.as_view(), name='area-cleaning-list-create'),
    path('area-cleaning/<int:pk>/', AreaCleaningDetailAPIView.as_view(), name='area-cleaning-detail'),
    
    path('search-all-senitizer/', AllSenitizersAPIView.as_view(), name='area-cleaning-detail'),
    
    path('cleaning-kpi/', CleaningKPIAPIView.as_view(), name='area-cleaning-detail'),
    
    path('cleaning/overall-score-snapshot/', CleaningOverallScoreAPIView.as_view(), name='cleaning-overall-score-snapshot'),
]