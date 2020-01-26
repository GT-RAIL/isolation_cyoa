import json
import logging
import traceback

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic.base import TemplateView as GenericTemplateView
from django.views.generic.edit import FormView as GenericFormView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator

from .models import User
from .models.domain import constants, State, Transition, display
from .forms import DemographicsForm, InstructionsTestForm, SurveyForm
from .utils import DropboxConnection


# Shared output across all views

logger = logging.getLogger(__name__)
dbx = DropboxConnection()


# Create your views here.

class CheckProgressMixin:
    """
    An mixin that checks the user's progress through the experiment and forces
    them to follow a certain trajectory

    Should probably write a test for this one
    """

    def dispatch(self, request, *args, **kwargs):
        allowed_pages = constants.STUDY_PROGRESS_STATES[request.user.study_progress]
        if request.user.is_staff or request.resolver_match.url_name in allowed_pages:
            # Allow the underlying views to take charge
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect(reverse(f'dining_room:{allowed_pages[0]}'))


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


@method_decorator(never_cache, name='dispatch')
class DemographicsFormView(FormView):
    """
    Display the demographics questionnaire form, validate it, and update the
    User object accordingly
    """
    template_name = 'dining_room/demographics.html'
    form_class = DemographicsForm
    success_url = reverse_lazy('dining_room:instructions')


@method_decorator(never_cache, name='dispatch')
class InstructionsView(TemplateView):
    """
    Display the instructions page
    """
    template_name = 'dining_room/instructions.html'


@method_decorator(never_cache, name='dispatch')
class InstructionsTestView(FormView):
    """
    Display the gold standard questions for the instructions and save the data
    """
    template_name = 'dining_room/test.html'
    form_class = InstructionsTestForm
    success_url = reverse_lazy('dining_room:study')


@method_decorator(never_cache, name='dispatch')
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

        # Create a dropbox file for the user, or mark that the user has
        # restarted the scenarios
        dbx.write_to_csv(request.user)

        # Update the time the user started the study
        request.user.date_started = timezone.now()
        request.user.save()
        return response


@method_decorator(never_cache, name='dispatch')
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


@method_decorator(never_cache, name='dispatch')
class CompleteView(TemplateView):
    """
    Show the final completion page to the user
    """
    template_name = 'dining_room/complete.html'


# API

def convert_mug_to_cup(value):
    """Helper function to convert a string from mug to cup"""
    if isinstance(value, str) and value.lower() == 'mug':
        return 'cup'
    else:
        return value


def convert_empty_gripper(value):
    if value == constants.EMPTY_GRIPPER:
        value = constants.EMPTY_GRIPPER_DISPLAY
    return value


def get_next_state_json(current_state, action):
    """
    Return the next state information given the current state and the action.
    If action is None, then simply return the current state as a JSON. We
    perform caching within this view function to save time

    Args:
        current_state (tuple/list) : the current state object as a tuple
        action (None / str) : the action to take

    Returns:
        next_state: The next state object
        next_state_json: JSON dictionary of the next state
    """
    current_state = State(current_state)

    # First check the cache for the answer
    cache_key = f"{'.'.join(current_state.tuple)}:{action}"
    cache_value = cache.get(cache_key)
    if cache_value is not None:
        return cache_value

    # Generate the JSON data
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
            { "attr": "Location", "value": display(next_state.relocalized_base_location) },
            { "attr": "Object in hand", "value": display(convert_mug_to_cup(convert_empty_gripper(next_state.gripper_state))) },
            { "attr": "Objects in view", "value": [display(convert_mug_to_cup(x)) for x in next_state.visible_objects] },
            { "attr": "Arm status", "value": display(transition.arm_status) },
        ],
        "valid_actions": sorted(next_state.get_valid_transitions().keys()),
        "dx_suggestions": ["cannot_pick"],
        "ax_suggestions": ["look_at_dt", "pick_bowl"],
        "action_result": action_result,
        "scenario_completed": next_state.is_end_state,
    }

    # Save the data to the cache
    cache.set(cache_key, next_state_json, timeout=None)

    # Return the dictionary
    return next_state_json


@require_POST
@csrf_exempt
@never_cache
def get_next_state(request):
    try:
        post_data = json.loads(request.body.decode('utf-8'))

        # Get the next state
        current_state_tuple = post_data.get('server_state_tuple')
        action = post_data.get('action')
        next_state_json = get_next_state_json(current_state_tuple, action)

        # Update the CSV with the incoming data (only if this is on django)
        if request.user.is_authenticated:
            dbx.write_to_csv(
                request.user,
                **{
                    "start_state": repr(State(current_state_tuple)),
                    "diagnoses": str(post_data.get('ui_state', {}).get('confirmed_dx')),
                    "diagnosis_certainty": post_data.get('ui_state', {}).get('dx_certainty'),
                    "action": action,
                    "next_state": repr(State(next_state_json['server_state_tuple'])),
                    "video_loaded_time": post_data.get('ui_state', {}).get('video_loaded_time'),
                    "video_stop_time": post_data.get('ui_state', {}).get('video_stop_time'),
                    "dx_selected_time": post_data.get('ui_state', {}).get('dx_selected_time'),
                    "dx_confirmed_time": post_data.get('ui_state', {}).get('dx_confirmed_time'),
                    "ax_selected_time": post_data.get('ui_state', {}).get('ax_selected_time'),
                }
            )

            # If the next state JSON says that the user is done, then mark that, else
            # complete the scenario based on if the user has exceeded max actions
            if next_state_json['scenario_completed']:
                request.user.scenario_completed = True
                request.user.save()
            elif post_data.get('ui_state', {}).get('selected_action_idx') >= constants.MAX_NUMBER_OF_ACTIONS:
                next_state_json['scenario_completed'] = True
                request.user.scenario_completed = False
                request.user.save()

        # Otherwise, simply check to see if we are over the limit of the maximum
        # number of actions
        elif post_data.get('ui_state', {}).get('selected_action_idx') >= constants.MAX_NUMBER_OF_ACTIONS:
            next_state_json['scenario_completed'] = True
    except Exception as e:
        trace = traceback.format_exc()
        logger.error(f"Error processing next state {e}:\n{trace}")
        if request.user.is_authenticated:
            request.user.ignore_data_reason = trace
            request.user.save()
        next_state_json = {
            'scenario_completed': True
        }

    # Return
    return JsonResponse(next_state_json)
