#!/usr/bin/env python
# Data Loader

import numpy as np
import pandas as pd

from django.conf import settings
from django.db.models import Q
from django.forms.models import model_to_dict
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
        # Get rid of useless columns
        del data['amt_worker_id']
        del data['password']
        del data['unique_key']

        # Get some indicators
        data['noise_level'] = (user.noise_level * 10)
        data['has_noise'] = user.noise_level > 0
        data['has_dx'] = user.show_dx_suggestions
        data['has_ax'] = user.show_ax_suggestions
        data['has_dxax'] = user.show_dx_suggestions and user.show_ax_suggestions
        data['has_ax_only'] = user.show_ax_suggestions and not user.show_dx_suggestions
        data['has_dx_only'] = user.show_dx_suggestions and not user.show_ax_suggestions
        data['has_suggestions'] = user.show_ax_suggestions or user.show_dx_suggestions
        data['suggestion_type'] = (
            'AX' if user.show_ax_suggestions and not user.show_dx_suggestions else (
                'DX' if not user.show_ax_suggestions and user.show_dx_suggestions else (
                    'DXAX' if user.show_ax_suggestions and user.show_dx_suggestions else 'NONE'
                )
            )
        )

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

        # Get summary stats from actions
        data['decision_duration'] = []
        data['dx_decision_duration'] = []
        data['ax_decision_duration'] = []
        data['diagnosis_certainty'] = []

        # Get the data from the actions
        for action in user.studyaction_set.order_by('start_timestamp'):
            data['decision_duration'].append(action.decision_duration.total_seconds())
            data['dx_decision_duration'].append(action.decision_duration.total_seconds())
            data['ax_decision_duration'].append(action.decision_duration.total_seconds())

            data['diagnosis_certainty'].append(action.diagnosis_certainty)

            data['num_dx_optimal'] += 1 if action.chose_dx_optimal else 0
            data['num_ax_optimal'] += 1 if action.chose_ax_optimal else 0

            if user.show_dx_suggestions:
                data['num_dx_corrupt'] += 1 if action.corrupted_dx_suggestions else 0
                data['num_dx_followed'] += 1 if action.chose_dx_suggestion else 0

            if user.show_ax_suggestions:
                data['num_ax_corrupt'] += 1 if action.corrupted_ax_suggestions else 0
                data['num_ax_followed'] += 1 if action.chose_ax_suggestion else 0

        # Summary stats for the time per action
        data['decision_duration_sum'] = np.sum(data['decision_duration'])
        data['dx_decision_duration_sum'] = np.sum(data['dx_decision_duration'])
        data['ax_decision_duration_sum'] = np.sum(data['ax_decision_duration'])
        data['decision_duration_mean'] = np.mean(data['decision_duration'])
        data['dx_decision_duration_mean'] = np.mean(data['dx_decision_duration'])
        data['ax_decision_duration_mean'] = np.mean(data['ax_decision_duration'])
        data['decision_duration_median'] = np.median(data['decision_duration'])
        data['dx_decision_duration_median'] = np.median(data['dx_decision_duration'])
        data['ax_decision_duration_median'] = np.median(data['ax_decision_duration'])

        del data['decision_duration']
        del data['dx_decision_duration']
        del data['ax_decision_duration']

        # Summary stats of the diagnosis certainty
        data['diagnosis_certainty_sum'] = np.sum(data['diagnosis_certainty'])
        data['diagnosis_certainty_mean'] = np.mean(data['diagnosis_certainty'])
        data['diagnosis_certainty_median'] = np.median(data['diagnosis_certainty'])
        del data['diagnosis_certainty']

        # Add the num_actions_diff metric
        data['num_actions_diff'] = data['num_actions'] - data['num_optimal']
        data['frac_actions_diff'] = data['num_actions_diff'] / (20 - data['num_optimal'])

        # Get normalized metric values
        data['frac_dx_optimal'] = data['num_dx_optimal'] / data['num_actions']
        data['frac_dx_followed'] = (data['num_dx_followed'] / data['num_actions']) if user.show_dx_suggestions else None
        data['frac_ax_optimal'] = data['num_ax_optimal'] / data['num_actions']
        data['frac_ax_followed'] = (data['num_ax_followed'] / data['num_actions']) if user.show_ax_suggestions else None

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
        data['action_idx'] = action.action_idx

        # Create State, Action, Transition objects
        start_state = State(eval(action.start_state))
        next_state = State(eval(action.next_state))
        transition = Transition(start_state, action.action, next_state)

        # Get data from the user
        data.update(model_to_dict(action.user))
        del data['amt_worker_id']
        del data['password']
        del data['unique_key']
        data['id'] = action.pk

        data['num_actions'] = action.user.num_actions
        if action.user.studyaction_set.filter(browser_refreshed=True).count() > 0:
            data['scenario_completed'] = False
            data['num_actions'] = 20

        # The primary independent variables
        data['noise_level'] = (action.user.noise_level * 10)
        data['has_noise'] = action.user.noise_level > 0
        data['has_dx'] = action.user.show_dx_suggestions
        data['has_ax'] = action.user.show_ax_suggestions
        data['has_dxax'] = action.user.show_dx_suggestions and action.user.show_ax_suggestions
        data['has_ax_only'] = action.user.show_ax_suggestions and not action.user.show_dx_suggestions
        data['has_dx_only'] = action.user.show_dx_suggestions and not action.user.show_ax_suggestions
        data['has_suggestions'] = action.user.show_ax_suggestions or action.user.show_dx_suggestions
        data['suggestion_type'] = (
            'AX' if action.user.show_ax_suggestions and not action.user.show_dx_suggestions else (
                'DX' if not action.user.show_ax_suggestions and action.user.show_dx_suggestions else (
                    'DXAX' if action.user.show_ax_suggestions and action.user.show_dx_suggestions else 'NONE'
                )
            )
        )

        # Get some the inferred data in the user df
        optimal_sequence = constants.OPTIMAL_ACTION_SEQUENCES[action.user.start_condition]
        data['num_optimal'] = len(optimal_sequence)-1
        data['num_actions_diff'] = data['num_actions'] - data['num_optimal']
        data['frac_actions_diff'] = data['num_actions_diff'] / (20 - data['num_optimal'])

        # Get the durations
        data['duration'] = action.duration.total_seconds()
        data['dx_decision_duration'] = action.dx_decision_duration.total_seconds()
        data['ax_decision_duration'] = action.ax_decision_duration.total_seconds()
        data['decision_duration'] = action.decision_duration.total_seconds()
        data['frac_dx_decision_duration'] = data['dx_decision_duration'] / data['decision_duration']
        data['frac_ax_decision_duration'] = data['ax_decision_duration'] / data['decision_duration']

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

    # Update the state information so that it incorporates value counts
    state_counts = _cached_actions_df['start_state'].value_counts()
    action_counts = _cached_actions_df['action'].value_counts()
    _cached_actions_df['state_idx'] = _cached_actions_df['start_state'].apply(lambda x: state_counts[x])
    _cached_actions_df['action_val'] = _cached_actions_df['action'].apply(lambda x: action_counts[x])

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
