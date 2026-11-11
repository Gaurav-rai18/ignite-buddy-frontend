from django.urls import path
from .views import DocumentListCreateView, DocumentDetailView

urlpatterns = [
    path("", DocumentListCreateView.as_view(), name="documents-list-create"),
    path("<int:pk>/", DocumentDetailView.as_view(), name="documents-detail"),
]

