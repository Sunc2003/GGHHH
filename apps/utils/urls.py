# apps/utils/urls.py
from django.urls import path
from .views import TestSupabaseUploadView


urlpatterns = [
    path('test-upload/', TestSupabaseUploadView.as_view(), name='test_upload'),
    
   
   
]


