from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Correctly reference the custom logout view
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.login_view),  # Redirect root URL to login view

    path('delete_folder/', views.delete_folder, name='delete_folder'),
    path('download_folder/', views.download_folder, name='download_folder'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('view_file/', views.view_file, name='view_file'),
    path('download_file/', views.download_file, name='download_file'),
     path('search/', views.search, name='search')
]
