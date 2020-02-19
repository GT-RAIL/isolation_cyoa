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
        for user in users.order_by('study_condition'):
            # Assert that the user has actions
            assert user.studyaction_set.count() > 0, f"User {user} is missing actions"

            # Simulate the user's experience
            self._simulate_user(user)

            # Print a status message
            if verbosity > 0:
                self.stdout.write(f"Simulated suggestions for {user}")

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
        sim_user.save()

        # For each state visited by the user, simulate the suggestions
        prev_action = None
        start_state = State(user.start_condition.split('.'))
        suggestions_check = Suggestions()
        for action in actions:
            next_state = State(eval(action.start_state))

            # Get the next state and verify it
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
                    suggestions_check.ordered_diagnoses(start_state, prev_action)[0] not in action.dx_suggestions
                ):
                    action.corrupted_dx_suggestions = True

                if (
                    user.show_ax_suggestions and
                    suggestions_check.optimal_action(start_state, prev_action)[0] not in action.ax_suggestions
                ):
                    action.corrupted_ax_suggestions = True

            # Save the action
            action.save()
            prev_action = action.action
            start_state = State(eval(action.next_state))

        # Simulate the last suggestions call
        json = get_next_state_json(start_state.tuple, prev_action, sim_user)

        # Check the RNG state
        assert sim_user.rng_state == user.rng_state, \
            f"Mismatch end state... FML: {user}... {user.rng_state} != {sim_user.rng_state}"

