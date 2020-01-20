import json
import logging

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
from .models.domain import constants, State, Transition, display
from .forms import DemographicsForm, InstructionsTestForm, SurveyForm
from .utils import DropboxConnection


# Shared output across all views

logger = logging.getLogger(__name__)
dbx = DropboxConnection()


# Common methods

# TODO: Cache this JSON function because it is expensive to calculate
def get_next_state_json(current_state, action):
    """
    Return the next state information given the current state and the action.
    If action is None, then simply return the current state as a JSON

    Args:
        current_state (state_tuple) : the current state as tuple
        action (None / str) : the action to take

    Returns:
        next_state_json: JSON dictionary of the next state
    """
    current_state = State(current_state)

    action_result = True
    if action is None:
        next_state = current_state
        transition = Transition(None, None, current_state)
    else:
        next_state = Transition.get_end_state(current_state, action)
        if next_state is None:
            action_result = False
            transition = Transition(None, None, current_state)
        else:
            transition = Transition(current_state, action, next_state)

    # Create the JSON dictionary
    next_state_json = {
        "server_state_tuple": next_state.tuple,
        "video_link": dbx.video_links[transition.video_name],
        "robot_beliefs": [
            { "attr": "Location", "value": display(constants.LOCATION_NAMES[next_state.base_location]) },
            { "attr": "Object in gripper", "value": display(next_state.gripper_state) },
            { "attr": "Objects in view", "value": [display(x) for x in next_state.visible_objects] },
            { "attr": "Arm status", "value": display(transition.arm_status) },
        ],
        "valid_actions": sorted(next_state.get_valid_transitions().keys()),
        "dx_suggestions": [],
        "ax_suggestions": [],
        "action_result": action_result,
        "scenario_completed": next_state.is_end_state,
    }

    # Return the dictionary
    return next_state_json


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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['actions_constant'] = json.dumps(constants.ACTIONS)
        context['diagnoses_constant'] = json.dumps(constants.DIAGNOSES)

        # Get the state json
        start_state_tuple = self.request.user.start_condition.split('.')
        start_state_json = get_next_state_json(start_state_tuple, None)
        context['scenario_state'] = json.dumps(start_state_json)

        return context

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


# API

@login_required
def study_json_template(request):
    return JsonResponse({'videos': True})
