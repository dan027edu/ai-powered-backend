from django.urls import path
from .views import (
    DocumentProcessView, 
    DocumentListView, 
    DocumentStatusView, 
    NotificationView,
    DocumentFileView,
    DocumentDetailView
)

urlpatterns = [
    path('documents/process/', DocumentProcessView.as_view(), name='document-process'),
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/<str:document_id>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<str:document_id>/file/', DocumentFileView.as_view(), name='document-file'),
    path('documents/<str:document_id>/status/', DocumentStatusView.as_view(), name='document-status'),
    path('notifications/', NotificationView.as_view(), name='notifications'),
    path('notifications/<int:notification_id>/', NotificationView.as_view(), name='notification-update'),
]