from django.urls import path
from . import views


urlpatterns = [
    path('ingest/', views.IngestAPIView.as_view(), name='ingest'),
    path('extract/', views.ExtractAPIView.as_view(), name='extract'),
]
