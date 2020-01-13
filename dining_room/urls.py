from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='dining_room/login.html'), name='login'),
    path('demographics', views.demographics, name='demographics'),
    path('instructions', views.instructions, name='instructions'),
    path('logout', auth_views.logout_then_login, name='logout'),
]
