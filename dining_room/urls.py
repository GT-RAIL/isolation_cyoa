from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dining_room'
urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='dining_room/login.html', redirect_authenticated_user=True), name='login'),
    path('demographics', views.DemographicsFormView.as_view(), name='demographics'),
    path('instructions', views.InstructionsView.as_view(), name='instructions'),
    path('instructions/t', views.InstructionsTestView.as_view(), name='instructions_t'),
    path('study', views.StudyView.as_view(), name='study'),
    path('survey', views.SurveyView.as_view(), name='survey'),
    path('complete', views.CompleteView.as_view(), name='complete'),
    path('logout', auth_views.logout_then_login, name='logout'),
]
