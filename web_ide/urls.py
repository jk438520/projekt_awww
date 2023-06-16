from django.urls import path

from . import views

app_name = 'web_ide'

urlpatterns = [
    path('file/<int:pk>/', views.FileView.as_view(), name='file'),
    path('file_tree/', views.FileTreeView.as_view(), name='file_tree'),
    path('compile/', views.CompileView.as_view(), name='compile'),
    path('delete/', views.DeleteView.as_view(), name='delete'),
    path('add/', views.AddView.as_view(), name='add'),
]
