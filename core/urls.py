from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.UploadView.as_view(), name='upload'),
    path('api/upload/', views.ProcessImagesView.as_view(), name='api_upload'),
    path('api/result/<int:pk>/', views.GetResultView.as_view(), name='api_result'),
]