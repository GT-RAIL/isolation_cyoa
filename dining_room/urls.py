from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'dining_room'
urlpatterns = [
    path('', views.LoginView.as_view(), name='login'),
    path('create', views.create, name='create'),
    path('demographics', views.DemographicsFormView.as_view(), name='demographics'),
    path('instructions', views.InstructionsView.as_view(), name='instructions'),
    path('test', views.InstructionsTestView.as_view(), name='test'),
    path('study', views.StudyView.as_view(), name='study'),
    path('survey', views.SurveyView.as_view(), name='survey'),
    path('complete', views.CompleteView.as_view(), name='complete'),
    path('logout', auth_views.logout_then_login, name='logout'),

    # XHR
    path('_/next_state', views.get_next_state, name='xhr_next_state'),
]
