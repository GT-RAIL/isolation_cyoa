#!/usr/bin/env python
# Figure out the expected suggestions that people might've seen and whether
# those suggestions might've been corrupted

import os
import sys
import copy
import pytz
import datetime
import traceback

import numpy as np

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from dining_room import constants
from dining_room.models import User, StudyManagement, StudyAction
from dining_room.models.domain import State, Transition, Suggestions
from dining_room.views import get_next_state_json


# Create the Command class

class Command(BaseCommand):
    """
    Fetch the actions data from dropbox, and replay the suggestions the user
    might've seen
    """

    help = "Load actions data from dropbox replay the suggestions a user might've seen. Run `sync_actions` before this command"

    V1_NOISE_USAGE_CONDITIONS = {
        User.StudyConditions.BASELINE,
        User.StudyConditions.DX_100,
        User.StudyConditions.AX_100,
        User.StudyConditions.DXAX_100,
        User.StudyConditions.DX_90,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('-a', '--all', action='store_true', help='Whether to simulate suggestions for all users, or only those with valid / relevant data')

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        if options['all']:
            users = User.objects.filter(is_staff=False).exclude(studyaction=None)
        else:
            users = User.objects.filter(
                Q(is_staff=False) &
                Q(date_survey_completed__isnull=False) &
                (Q(ignore_data_reason__isnull=True) | Q(ignore_data_reason=''))
            )

        self.stdout.write(f"Simulating experiences of {users.count()} users")

        # Create a sim user
        try:
            sim_user = User.objects.get(username='sim_user')
        except Exception as e:
            sim_user = User.objects.create_user('sim_user', 'sim_user')
            sim_user.save()

        # Iterate through the users and get their data
        for uidx, user in enumerate(users.order_by('study_condition')):
            # Assert that the user has actions
            assert user.studyaction_set.count() > 0, f"User {user} is missing actions"

            # Simulate the user's experience
            self._simulate_user(user)

            # Print a status message
            if verbosity > 0:
                self.stdout.write(f"({uidx+1}/{len(users)}) Simulated suggestions for {user}")

        # Delete the sim user
        sim_user.refresh_from_db()
        sim_user.delete()

        # Print a completion message
        self.stdout.write(self.style.SUCCESS("Suggestions synchronized!"))

    def _simulate_user(self, user):
        """Simulate the user's experience"""
        actions = user.studyaction_set.order_by('start_timestamp')

        # Get the simulated user and reset them
        sim_user = User.objects.get(username='sim_user')
        sim_user.study_condition = user.study_condition
        sim_user.start_condition = user.start_condition
        sim_user.rng_state = Suggestions.DEFAULT_RNG_SEED
        sim_user.number_state_requests = -1
        sim_user.save()

        # For each state visited by the user, simulate the suggestions
        prev_action = None
        start_state = State(user.start_condition.split('.'))
        schk = Suggestions()  # Just a means to get the optimal alternatives
        for action in actions:
            next_state = State(eval(action.start_state))

            # Get the next state and verify it
            if sim_user.study_condition in Command.V1_NOISE_USAGE_CONDITIONS:
                # Send an empty user, then update the json with the simulated
                # suggestions from the old way of doing things
                json = get_next_state_json(start_state.tuple, prev_action, None)
                json.update(self._v1_noise_get_suggestions_json(next_state, sim_user))
            else:
                json = get_next_state_json(start_state.tuple, prev_action, sim_user)

            assert tuple(json['server_state_tuple']) == next_state.tuple, \
                f"({start_state.tuple}, {prev_action}): {json['server_state_tuple']} != {next_state.tuple}"

            # Add the suggestions
            if user.show_dx_suggestions:
                action.dx_suggestions = json['dx_suggestions']

            if user.show_ax_suggestions:
                action.ax_suggestions = json['ax_suggestions']

            # Add a boolean if the data was corrupted
            if user.noise_level > 0:
                if (
                    user.show_dx_suggestions and
                    schk.ordered_diagnoses(start_state, prev_action)[0] not in action.dx_suggestions
                ):
                    action.corrupted_dx_suggestions = True

                if (
                    user.show_ax_suggestions and
                    schk.optimal_action(start_state, prev_action)[0] not in action.ax_suggestions
                ):
                    action.corrupted_ax_suggestions = True

            # Save the action
            action.save()
            prev_action = action.action
            start_state = State(eval(action.next_state))

        # Simulate the last suggestions call
        if sim_user.study_condition in Command.V1_NOISE_USAGE_CONDITIONS:
            json = get_next_state_json(start_state.tuple, prev_action, None)
            json.update(self._v1_noise_get_suggestions_json(start_state, sim_user))
        else:
            json = get_next_state_json(start_state.tuple, prev_action, sim_user)

        # Check the RNG state
        try:
            assert sim_user.rng_state == user.rng_state, \
                f"Mismatch end state... FML: {user}... {user.rng_state} != {sim_user.rng_state}"
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{e}"))
            raise

    def _v1_noise_get_suggestions_json(self, state, user):
        """Use the old style of garnering suggestions from the server"""
        suggestions_json = {}
        user.refresh_from_db()
        suggestions_provider = Suggestions(user)

        def add_noise_and_pad(suggestions, alternatives, pad):
            """The old definition of the noise + pad function"""
            pad = pad or len(suggestions)
            should_corrupt = (suggestions_provider.rng.uniform() < user.noise_level)
            if should_corrupt:
                suggestions = suggestions_provider.rng.choice(alternatives, size=len(suggestions), replace=False).tolist()

            alternatives = set(alternatives) - set(suggestions)
            while len(suggestions) < pad:
                suggestions.append(suggestions_provider.rng.choice(list(sorted(alternatives))))
                alternatives.discard(suggestions[-1])

            return suggestions

        # First add the DX suggestions
        if user.show_dx_suggestions:
            suggestions = suggestions_provider.ordered_diagnoses(state, None, accumulate=True)
        else:
            suggestions = []

        alternatives = [x for x in constants.DIAGNOSES.keys() if x not in suggestions]
        suggestions = add_noise_and_pad(
            suggestions[:user.study_management.max_dx_suggestions],
            alternatives,
            user.study_management.max_dx_suggestions if user.study_management.pad_suggestions else None
        )

        suggestions_json['dx_suggestions'] = suggestions

        # Update the RNG
        user.rng_state = Suggestions.get_next_rng_seed(suggestions_provider.rng)
        user.save()

        # Second the AX suggestions
        if user.show_ax_suggestions:
            suggestions = suggestions_provider.optimal_action(state, None)
        else:
            suggestions = []

        valid_actions = state.get_valid_actions()
        alternatives = [k for k, v in valid_actions.items() if (k not in suggestions and v)]
        suggestions  = add_noise_and_pad(
            suggestions[:user.study_management.max_ax_suggestions],
            alternatives,
            user.study_management.max_ax_suggestions if user.study_management.pad_suggestions else None
        )

        suggestions_json['ax_suggestions'] = suggestions

        # Update the RNG
        user.rng_state = Suggestions.get_next_rng_seed(suggestions_provider.rng)
        user.save()

        # Return the JSON
        return suggestions_json
