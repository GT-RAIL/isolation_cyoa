from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dining_room'
urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='dining_room/login.html'), name='login'),
    path('demographics', views.DemographicsFormView.as_view(), name='demographics'),
    path('instructions', views.instructions, name='instructions'),
    path('instructions/t', views.InstructionsTestView.as_view(), name='instructions_t'),
    path('study', views.study_template, name='study'),
    path('logout', auth_views.logout_then_login, name='logout'),
]
