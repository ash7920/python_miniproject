# urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.splash, name='splash'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('connections/', views.connections, name='connections'),
    path('send_connection/<int:profile_id>/', views.send_connection, name='send_connection'),
    path('accept_connection/<int:conn_id>/', views.accept_request, name='accept_connection'),
    path('reject_connection/<int:conn_id>/', views.reject_request, name='reject_connection'),
    path('send_request/<int:user_id>/', views.send_request, name='send_request'),
    path('accept_request/<int:conn_id>/', views.accept_request, name='accept_request'),
    #path('upload_note/', views.upload_note, name='upload_note'),
    #path('view_notes/', views.view_notes, name='view_notes'),
    path('tasks/', views.tasks, name='tasks'),
    path('toggle_task/<int:task_id>/', views.toggle_task, name='toggle_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('reject_request/<int:conn_id>/', views.reject_request, name='reject_request'),
    path('schedule_meeting/<int:conn_id>/', views.schedule_meeting, name='schedule_meeting'),
    path('connections/unique/', views.get_unique_connections, name='get_unique_connections'),
    path('complete_meeting/<int:meeting_id>/', views.complete_meeting, name='complete_meeting'),
    path('notes_dashboard/', views.notes_dashboard, name='notes_dashboard'),
    path('delete_note/<int:note_id>/', views.delete_note, name='delete_note'),

]
