from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.login_view), 

    path('delete_folder/', views.delete_folder, name='delete_folder'),
    path('download_folder/', views.download_folder, name='download_folder'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('view_file/', views.view_file, name='view_file'),
    path('download_file/', views.download_file, name='download_file'),
    path('search/', views.search_files, name='search'),
    path('download/', views.download, name='download'),
    path('users/', views.load_users, name="users"),
    path('logs/', views.load_user_activities, name='load_user_activities'),
    path('logs/<str:log_name>/', views.get_log_content, name='get_log_content'),

   # handle password reset using django builtin authentication with custom interface/template
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='passwordreset/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='passwordreset/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='passwordreset/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='passwordreset/password_reset_complete.html'), name='password_reset_complete'),
]
