from django.urls import path
from . import views



urlpatterns = [
    path('ingest/', views.IngestAPIView.as_view(), name='ingest'),
    
]
