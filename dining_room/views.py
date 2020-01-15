import os
import csv
import time
import dropbox

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView as GenericTemplateView
from django.views.generic.edit import FormView as GenericFormView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .models import User
from .forms import DemographicsForm, InstructionsTestForm, SurveyForm


# Create your views here.

class CheckProgressMixin:
    """
    An mixin that checks the user's progress through the experiment and forces
    them to follow a certain trajectory

    Should probably write a test for this one
    """

    def dispatch(self, request, *args, **kwargs):
        allowed_locations = None
        if request.user.date_demographics_completed is None:
            # If demographics haven't been completed, redirect to demographics
            allowed_locations = ['demographics']

        elif (request.user.date_started is None or request.user.date_finished is None or request.user.date_survey_completed is None):
            # If the study has not been completed, but demographics have been,
            # then redirect to the instructions and restart the study
            allowed_locations = ['instructions', 'test', 'study', 'survey']

        elif request.user.date_survey_completed is not None:
            # If the user has completed the study, and the survey, then redirect
            # to the completed page
            allowed_locations = ['complete']

        if request.resolver_match.url_name in allowed_locations:
            # Allow the underlying views to take charge
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect(reverse(f'dining_room:{allowed_locations[0]}'))


class TemplateView(LoginRequiredMixin, CheckProgressMixin, GenericTemplateView):
    """
    An abstract class view for all the static pages in our app
    """
    pass


class FormView(LoginRequiredMixin, CheckProgressMixin, GenericFormView):
    """
    An abstract class view for all the pages with ModelForms in our app
    """

    def get_form_kwargs(self):
        """Override the instance using the request"""
        kwargs = super().get_form_kwargs()

        # If this object has been saved before, fetch that, else get the user
        # from the request
        if hasattr(self, 'object'):
            kwargs['instance'] = self.object
        else:
            assert hasattr(self.request, 'user') and self.request.user.is_authenticated, \
                f"The request ({self.request}) does not have an authenticated user"
            kwargs['instance'] = self.request.user

        return kwargs

    def form_valid(self, form):
        """
        The form is valid, save the instance
        """
        self.object = form.save()
        return super().form_valid(form)


class DemographicsFormView(FormView):
    """
    Display the demographics questionnaire form, validate it, and update the
    User object accordingly
    """
    template_name = 'dining_room/demographics.html'
    form_class = DemographicsForm
    success_url = reverse_lazy('dining_room:instructions')


class InstructionsView(TemplateView):
    """
    Display the instructions page
    """
    template_name = 'dining_room/instructions.html'


class InstructionsTestView(FormView):
    """
    Display the gold standard questions for the instructions and save the data
    """
    template_name = 'dining_room/test.html'
    form_class = InstructionsTestForm
    success_url = reverse_lazy('dining_room:study')


class StudyView(TemplateView):
    """
    Most of the study template will be handled by AJAX. This view simply sets
    up the HTML page within which the JS will work
    """
    template_name = 'dining_room/study.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            return response

        # Update the time the user started the study
        request.user.date_started = timezone.now()
        request.user.save()
        return response


class SurveyView(FormView):
    """
    Process the post completion survey. Also update the timestamps of the user
    """
    template_name = 'dining_room/survey.html'
    form_class = SurveyForm
    success_url = reverse_lazy('dining_room:complete')

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if isinstance(response, HttpResponseRedirect):
            return response

        # If we are requesting this form for the first time, we've probably just
        # completed the study; update the timestamp
        if request.method == 'GET':
            request.user.date_finished = timezone.now()
            request.user.save()
        return response


class CompleteView(TemplateView):
    """
    Show the final completion page to the user
    """
    template_name = 'dining_room/complete.html'


# The API views begin here. Therefore, we should load in the dropbox data

dbx = dropbox.Dropbox(os.getenv(settings.DROPBOX_ENV_KEY))

# Begin with a constant dictionary for the video links. Update the dictionary
# if the file does not exist, or if the this server was started more than 15 min
# after the last modification timestamp for the file
_local_links_file = os.path.join("/tmp", settings.DROPBOX_VIDEO_LINKS_FILE)
if not os.path.exists(_local_links_file) or os.path.getmtime(_local_links_file) < (time.time() - 900):
    dbx.files_download_to_file(_local_links_file, os.path.join('/', settings.DROPBOX_FOLDER_NAME, 'data', settings.DROPBOX_VIDEO_LINKS_FILE))

_links_data = []
with open(_local_links_file, 'r') as fd:
    _reader = csv.reader(fd)
    for _row in _reader:
        _links_data.append(_row)

# The links data is stored in this variable
VIDEO_LINKS = { _l[0]: _l[-1] for _l in _links_data }


@login_required
def study_json_template(request):
    return JsonResponse({'videos': True})
