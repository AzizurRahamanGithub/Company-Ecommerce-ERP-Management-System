from django.urls import path
from .views import ProductionListCreateAPIView, ProductionDetailAPIView, ProductionVisualizationAPIView, YieldVisualizationAPIView

urlpatterns = [
    path('production/', ProductionListCreateAPIView.as_view(), name='production-list-create'),
    path('production/<int:pk>/', ProductionDetailAPIView.as_view(), name='production-detail'),
    
    path('production/visualization/', ProductionVisualizationAPIView.as_view()),
    path('yield/visualization/', YieldVisualizationAPIView.as_view(), name='yield-visualization'),
]
