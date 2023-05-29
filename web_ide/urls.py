from django.urls import path

from . import views

app_name = 'web_ide'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.FileView.as_view(), name='file'),
    path('compile/<int:pk>', views.CompileView.as_view(), name='compile'),
    path('add_file/', views.AddFileView.as_view(), name='add_file'),
    path('add_file/<int:pk>', views.AddFileView.as_view(), name='add_file'),
    path('add_directory/', views.AddDirectoryView.as_view(), name='add_directory'),
    path('add_directory/<int:pk>', views.AddDirectoryView.as_view(), name='add_directory'),
    path('delete/<int:pk>/<int:current_file>/', views.DeleteView.as_view(), name='delete'),
    path('delete/<int:pk>/', views.DeleteView.as_view(), name='delete'),
    path('add_or_remove_tree/', views.AddOrRemoveTreeView.as_view(), name='add_or_remove_tree'),
]
