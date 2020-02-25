#!/usr/bin/env python
# Data Loader

import numpy as np
import pandas as pd

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .. import constants
from ..models import User, StudyManagement, StudyAction
from ..models.domain import State, Transition, Suggestions

from .stat_tests import cronbach_alpha


# Constants

IS_STAFF_FILTER = Q(is_staff=False)
INVALID_FILTER = Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason='')


# The different functions

def load_valid_users():
    """Load valid users from the DB"""
    return User.objects.filter(IS_STAFF_FILTER & INVALID_FILTER).order_by('pk')


def load_valid_actions():
    """Load valid actions from the DB"""
    return StudyAction.objects.filter(user__in=load_valid_users()).order_by('user', 'start_timestamp')


# Cache results and reuse unless otherwise specified
_cached_users_df = None
_cached_actions_df = None


def get_users_df(*, users=None, use_cache=True):
    """
    Get information about the valid users as a data frame. A copy of a cache is
    used unless users is specified or use_cache is set to False
    """
    global _cached_users_df

    # Return a copy of the cache if possible
    if (users is None and use_cache) and _cached_users_df is not None:
        return _cached_users_df.copy()

    # Create a new df
    users = users or load_valid_users()
    _cached_users_df = users.values()

    # Add common information to the data frame
    for user, data in zip(users, _cached_users_df):
        # Get some indicators
        data['noise_level'] = (user.noise_level * 10)
        data['has_noise'] = user.noise_level > 0
        data['has_dx'] = user.show_dx_suggestions
        data['has_ax'] = user.show_ax_suggestions

        # Get meta information about the actions
        data['num_actions'] = user.num_actions
        data['num_refreshes'] = user.studyaction_set.filter(browser_refreshed=True).count()

        # Mark a refresh as incomplete and with 20 actions
        if data['num_refreshes'] > 0:
            data['num_actions'] = 20
            data['scenario_completed'] = False

        # Get the information tied to optimality
        optimal_sequence = constants.OPTIMAL_ACTION_SEQUENCES[user.start_condition]
        data['num_optimal'] = len(optimal_sequence)-1
        data['num_dx_optimal'] = 0
        data['num_ax_optimal'] = 0

        # Get counts of how well/poorly suggestions were followed
        data['num_dx_corrupt'] = 0 if user.show_dx_suggestions else None
        data['num_ax_corrupt'] = 0 if user.show_ax_suggestions else None
        data['num_dx_followed'] = 0 if user.show_dx_suggestions else None
        data['num_ax_followed'] = 0 if user.show_ax_suggestions else None

        for action in user.studyaction_set.order_by('start_timestamp'):
            data['num_dx_optimal'] += 1 if action.chose_dx_optimal else 0
            data['num_ax_optimal'] += 1 if action.chose_ax_optimal else 0

            if user.show_dx_suggestions:
                data['num_dx_corrupt'] += 1 if action.corrupted_dx_suggestions else 0
                data['num_dx_followed'] += 1 if action.chose_dx_suggestion else 0

            if user.show_ax_suggestions:
                data['num_ax_corrupt'] += 1 if action.corrupted_ax_suggestions else 0
                data['num_ax_followed'] += 1 if action.chose_ax_suggestion else 0

    # Make a dataframe out of the information
    _cached_users_df = pd.DataFrame(_cached_users_df)

    return _cached_users_df.copy()


def get_actions_df(*, actions=None, use_cache=True):
    """
    Get information about the valid actions as a data frame. A copy of a cache
    is used unless actions is specified or use_cache is set to False.

    Note that the actions df also contains information on each state
    """
    global _cached_actions_df

    # Return a copy of the cache if possible
    if (actions is None and use_cache) and _cached_actions_df is not None:
        return _cached_actions_df.copy()

    # Create a new df
    actions = actions or load_valid_actions()
    _cached_actions_df = actions.values()

    # Add commmon information to the data frames
    for action, data in zip(actions, _cached_actions_df):
        # Create State, Action, Transition objects
        start_state = State(eval(action.start_state))
        next_state = State(eval(action.next_state))
        transition = Transition(start_state, action.action, next_state)

        # Get data from the user
        data['start_condition'] = action.user.start_condition
        data['study_condition'] = action.user.study_condition
        data['scenario_completed'] = action.user.scenario_completed
        data['num_actions'] = action.user.num_actions
        if action.user.studyaction_set.filter(browser_refreshed=True).count() > 0:
            data['scenario_completed'] = False
            data['num_actions'] = 20

        # The primary independent variables
        data['noise_level'] = (action.user.noise_level * 10)
        data['has_noise'] = action.user.noise_level > 0
        data['has_dx'] = action.user.show_dx_suggestions
        data['has_ax'] = action.user.show_ax_suggestions

        # Get the durations
        data['action_idx'] = action.action_idx
        data['duration'] = action.duration.total_seconds()
        data['dx_decision_duration'] = action.dx_decision_duration.total_seconds()
        data['ax_decision_duration'] = action.ax_decision_duration.total_seconds()
        data['decision_duration'] = action.decision_duration.total_seconds()

        # Get the computed booleans
        data['chose_dx'] = action.chose_dx_suggestion
        data['chose_ax'] = action.chose_ax_suggestion
        data['optimal_dx'] = action.chose_dx_optimal
        data['optimal_ax'] = action.chose_ax_optimal

        # Widen out the data for each diagnosis
        for diagnosis in constants.DIAGNOSES.keys():
            data[f'{diagnosis}_selected'] = diagnosis in action.diagnoses

        # Add information about the state itself
        data['failed_to_place'] = (
            None if start_state.gripper_empty
            else (start_state.gripper_state != 'mug' and action.action != 'place')
        )

        data['gripper_empty'] = start_state.gripper_empty
        data['mislocalized'] = start_state.mislocalized
        data['mug_visible'] = 'mug' in start_state.visible_objects
        data['mug_graspable'] = 'mug' in start_state.graspable_objects
        data['bowl_visible'] = 'bowl' in start_state.visible_objects
        data['bowl_graspable'] = 'bowl' in start_state.graspable_objects
        data['jug_visible'] = 'jug' in start_state.visible_objects
        data['jug_graspable'] = 'jug' in start_state.graspable_objects
        data['arm_motion'] = transition.arm_status == constants.ARM_STATUS[1]
        data['robot_location'] = start_state.base_location

    # Make a data frame from the information
    _cached_actions_df = pd.DataFrame(_cached_actions_df)

    return _cached_actions_df.copy()


def get_survey_df(*, return_alpha=False, users=None, use_cache=True):
    """
    Get the survey data as a data frame. If return_alpha is specified, then
    return the Cronbach's Alpha value of each metric
    """
    survey_df = get_users_df(users=users, use_cache=use_cache)

    # Convert based on the valence of the scores (0-4)
    # Silly math formula: (score * valence) + (-4 * ((valence-1)/2))
    for field, valence in constants.SURVEY_QUESTION_VALENCE.items():
        survey_df[field] = (-4 * ((valence-1)/2)) + (survey_df[field] * valence)

    # Combine the different metrics. Calculate cronbach's alpha while we're at it
    alpha = {} if return_alpha else None
    for combination, fields in constants.SURVEY_COMBINATIONS.items():
        if return_alpha:
            alpha[combination] = cronbach_alpha(survey_df[fields].to_numpy())
        survey_df[combination] = survey_df.loc[:, fields].sum(axis=1)

    # The SUS has a special requirement of multiply by 2.5 for scaling
    survey_df['sus'] = survey_df['sus'] * 2.5

    # Return the df
    if return_alpha:
        return survey_df, alpha
    else:
        return survey_df
