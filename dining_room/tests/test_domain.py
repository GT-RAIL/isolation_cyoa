import os
import copy
import collections

import numpy as np

from django.test import SimpleTestCase, TestCase, Client

from dining_room import constants
from dining_room.models import User, StudyManagement
from dining_room.models.domain import State, Transition, Suggestions
from dining_room.views import get_next_state_json, get_suggestions_json


# The tests for various aspects of the Dining Room domain

class TransitionTestCase(SimpleTestCase):
    """
    Test the state transitions given sequences of actions
    """

    def _check_transition(self, expected, actual):
        """
        Check that the transition JSON dictionary contains the values in
        expected, with some special conditions depending on the keys that we
        are checking
        """
        for key, value in expected.items():
            # Check that the key exists
            self.assertIn(key, actual)

            # Coerce types, if necessary
            if isinstance(value, (list, tuple,)):
                value = tuple(value)
            if isinstance(actual[key], (list, tuple,)):
                actual[key] = tuple(actual[key])

            # Only compare the keys that we want to for transitions
            if key == 'video_link':
                self.assertEqual(value, os.path.basename(actual[key]))
            elif key in ['server_state_tuple', 'video_link', 'action_result', 'scenario_completed']:
                self.assertEqual(value, actual[key])

    def _run_test_action_sequence(self, start_state_tuple, action_sequence):
        """Run the series of actions specified in action_sequence until the end.
        At the end, make sure that we have indeed ended"""
        state_tuple = start_state_tuple
        for idx, (action, expected_values) in enumerate(action_sequence):
            next_json = get_next_state_json(state_tuple, action)
            expected_values['scenario_completed'] = (idx + 1 == len(action_sequence))
            try:
                self._check_transition(expected_values, next_json)
            except AssertionError as e:
                print(f"Error in step {idx+1}/{len(action_sequence)}: {e}")
                raise

            state_tuple = next_json['server_state_tuple']

    def test_optimal_action_sequences(self):
        """Test the optimal action sequences have expected transitions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            start_state_tuple = start_state_str.split('.')
            self._run_test_action_sequence(start_state_tuple, action_sequence)


class SuggestionsTestCase(TestCase):
    """
    Test the suggestions
    """

    def setUp(self):
        self.sm = StudyManagement.get_default()

        # Create a user and log them in
        self.user = User.objects.create_user('test_user', 'test_user')
        self.user.study_condition = User.StudyConditions.DXAX_100
        self.user.start_condition = User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG
        self.user.save()

        # # Log the user in on the client
        self.client.login(username='test_user', password='test_user')

        self.suggestions_provider = Suggestions(self.user)

        # Create an rng to shadow the user
        self.rng = np.random.default_rng(Suggestions.DEFAULT_RNG_SEED)

    def _check_suggestions(self, expected_suggestions, actual_suggestions, context={}):
        try:
            self.assertListEqual(expected_suggestions, actual_suggestions)
        except AssertionError as e:
            print(f"Error in {context.get('start_state_str')}, step {context.get('idx', 0) + 1}/{len(context.get('action_sequence', []))}: {e}")
            raise

    def _reset_rng(self, idx):
        """
        If idx = 0, reset the RNG to default. Else user the users' value. This
        refreshes the RNG values in the provider to simulate how we expect
        the RNG values to evolve as user requests come in
        """
        if idx == 0:
            self.user.rng_state = Suggestions.DEFAULT_RNG_SEED
            self.user.save()
            self.suggestions_provider = Suggestions(self.user)
            self.rng = np.random.default_rng(Suggestions.DEFAULT_RNG_SEED)
        else:
            self.user.refresh_from_db()
            self.suggestions_provider = Suggestions(self.user)
            self.rng = np.random.default_rng(self.user.rng_state)

    def test_ordered_diagnoses(self):
        """Test the ordered diagnosis method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])

                # Get the suggestions & test them
                suggestions = self.suggestions_provider.ordered_diagnoses(state, action, accumulate=True)
                self._check_suggestions(expected_values['dx_suggestions'], suggestions, locals())

                suggestions = self.suggestions_provider.ordered_diagnoses(state, action)
                self._check_suggestions([expected_values['dx_suggestions'][0]], suggestions, locals())

    def test_optimal_action(self):
        """Test the optimal actions method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])

                # Get the suggestions
                suggestions = self.suggestions_provider.optimal_action(state, action)

                # Test the suggestions
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                self._check_suggestions(expected_suggestions, suggestions, locals())

    def test_multiple_suggestions_without_padding(self):
        """Test the return of multiple suggestions without padding to ensure a
        constant number of suggestions at all timesteps"""
        self.sm.max_dx_suggestions = 2
        self.sm.max_ax_suggestions = 3
        self.sm.save()
        self.user.refresh_from_db()

        # Refresh the values in the suggestions provider
        self.suggestions_provider = Suggestions(self.user)

        for start_state, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]

                suggestions = self.suggestions_provider.suggest_dx(state, action)
                self._check_suggestions(expected_values['dx_suggestions'][:self.sm.max_dx_suggestions], suggestions, locals())

                suggestions = self.suggestions_provider.suggest_ax(state, action)
                self._check_suggestions(expected_suggestions, suggestions, locals())


    def test_noisy_dx_suggestions_no_padding(self):
        """Test the addition of noise to the DX suggestions, without adding
        padding"""
        self.user.study_condition = User.StudyConditions.DXAX_90
        self.user.save()
        self.assertEqual(0.1, self.user.noise_level)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():

            for idx, (action, expected_values) in enumerate(action_sequence):
                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])

                # Predict if we will see noise
                will_corrupt = (self.rng.uniform() < self.user.noise_level)
                alternatives = set([x for x in constants.DIAGNOSES.keys() if x not in expected_values['dx_suggestions']])
                if will_corrupt:
                    # Move the rng forward
                    x = self.rng.choice(list(alternatives),
                                        size=min(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions),
                                        replace=False)
                    alternatives = alternatives - set(x)

                # Then get the suggestions and check if they are corrupted
                suggestions = self.suggestions_provider.suggest_dx(state, action)
                if will_corrupt:
                    self.assertEqual(min(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions), len(suggestions))
                    for suggestion in suggestions:
                        self.assertNotIn(suggestion, expected_values['dx_suggestions'])
                else:
                    self._check_suggestions(expected_values['dx_suggestions'][:self.sm.max_dx_suggestions], suggestions, locals())

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

    def test_noisy_ax_suggestions_no_padding(self):
        """Test the addition of noise to the AX suggestions, without adding
        padding"""
        self.user.study_condition = User.StudyConditions.DXAX_90
        self.user.save()
        self.assertEqual(0.1, self.user.noise_level)

        # Refresh the values in the provider
        self.suggestions_provider = Suggestions(self.user)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                valid_actions_check = state.get_valid_actions()
                alternatives = set([k for k, v in valid_actions_check.items() if (k not in expected_suggestions and v)])

                # Predict if we will see noise
                will_corrupt = (self.rng.uniform() < self.user.noise_level)
                if will_corrupt and idx < len(action_sequence)-1:
                    # Move the rng forward
                    x = self.rng.choice(list(alternatives),
                                        size=min(len(expected_suggestions), self.sm.max_ax_suggestions),
                                        replace=False)
                    alternatives = alternatives - set(x)

                # Then get the suggestions and check if they are corrupted
                suggestions = self.suggestions_provider.suggest_ax(state, action)
                if will_corrupt:
                    self.assertEqual(min(self.sm.max_ax_suggestions, len(expected_suggestions)), len(suggestions))
                    for suggestion in suggestions:
                        self.assertNotIn(suggestion, expected_suggestions)
                else:
                    self._check_suggestions(expected_suggestions, suggestions, locals())

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

    def test_multiple_suggestions_with_padding(self):
        """Test multiple suggestions with padding, but no noise"""
        self.sm.max_dx_suggestions = 3
        self.sm.max_ax_suggestions = 3
        self.sm.pad_suggestions = True
        self.sm.save()
        self.user.refresh_from_db()

        # Refresh the values in the suggestions provider
        self.suggestions_provider = Suggestions(self.user)

        for start_state, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]

                # Check just the length of the suggestions and that all the
                # suggestions are in the padded suggestions
                suggestions = self.suggestions_provider.suggest_dx(state, action)
                self.assertEqual(self.sm.max_dx_suggestions, len(suggestions))
                for suggestion in expected_values['dx_suggestions'][:self.sm.max_dx_suggestions]:
                    self.assertIn(suggestion, suggestions)

                suggestions = self.suggestions_provider.suggest_ax(state, action)
                self.assertEqual(self.sm.max_ax_suggestions, len(suggestions))
                for suggestion in expected_suggestions:
                    self.assertIn(suggestion, suggestions)

    def test_multiple_with_noise_and_padding(self):
        """Test multiple suggestions with padding and noise"""
        self.sm.max_dx_suggestions = 3
        self.sm.max_ax_suggestions = 4
        self.sm.pad_suggestions = True
        self.sm.save()

        self.user.study_condition = User.StudyConditions.DXAX_90
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(0.1, self.user.noise_level)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])

                # First we do the DX
                # Predict if we will see noise
                alternatives = set([x for x in constants.DIAGNOSES.keys() if x not in expected_values['dx_suggestions']])
                will_corrupt = (self.rng.uniform() < self.user.noise_level)
                if will_corrupt:
                    # Move the rng forward
                    x = self.rng.choice(list(alternatives),
                                        size=min(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions),
                                        replace=False)
                    alternatives = alternatives - set(x)

                # Then update the rng if we need to pad
                for _ in range(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions):
                    x = self.rng.choice(list(alternatives))
                    alternatives.discard(x)

                # Then get the suggestions and check if they are corrupted
                suggestions = self.suggestions_provider.suggest_dx(state, action)
                self.assertEqual(self.sm.max_dx_suggestions, len(suggestions))
                for suggestion in expected_values['dx_suggestions'][:self.sm.max_dx_suggestions]:
                    if will_corrupt:
                        self.assertNotIn(suggestion, suggestions)
                    else:
                        self.assertIn(suggestion, suggestions)

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

                # Then we do the AX
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                valid_actions_check = state.get_valid_actions()
                alternatives = set([k for k, v in valid_actions_check.items() if (k not in expected_suggestions and v)])

                # Predict if we will see noise
                will_corrupt = (self.rng.uniform() < self.user.noise_level)
                if will_corrupt and idx < len(action_sequence)-1:
                    # Move the rng one forward
                    x = self.rng.choice(list(alternatives),
                                        size=min(len(expected_suggestions), self.sm.max_ax_suggestions),
                                        replace=False)
                    alternatives = alternatives - set(x)

                # Then update the rng based on the padding
                for _ in range(len(expected_suggestions), self.sm.max_ax_suggestions):
                    x = self.rng.choice(list(alternatives))
                    alternatives.discard(x)

                # Then get the suggestions and check if they are corrupted
                suggestions = self.suggestions_provider.suggest_ax(state, action)
                self.assertEqual(self.sm.max_ax_suggestions, len(suggestions))
                for suggestion in expected_suggestions:
                    if will_corrupt:
                        self.assertNotIn(suggestion, suggestions)
                    else:
                        self.assertIn(suggestion, suggestions)

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

    def test_all_noise_conditions_see_noise(self):
        """Test that all the noise conditions actually do see noise"""
        # Iterate through the study conditions
        for study_condition in [User.StudyConditions.DX_90, User.StudyConditions.AX_90, User.StudyConditions.DXAX_90]:
            self.user.study_condition = study_condition
            self.user.save()

            # Then run the same rigamarole of going testing noise without
            # padding
            for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
                encountered_noise = False

                # There has to be some noise before the end of the optimal
                # action sequence
                for idx, (action, expected_values) in enumerate(action_sequence[:-1]):
                    self._reset_rng(idx)

                    state = State(expected_values['server_state_tuple'])

                    # If DX should be shown, then calculate the noise probabilty
                    if self.user.show_dx_suggestions:
                        alternatives = set([x for x in constants.DIAGNOSES.keys() if x not in expected_values['dx_suggestions']])

                        will_corrupt = (self.rng.uniform() < self.user.noise_level)
                        if will_corrupt and idx < len(action_sequence)-1:
                            encountered_noise = True
                            # Move the rng forward
                            x = self.rng.choice(list(alternatives),
                                                size=min(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions),
                                                replace=False)
                            alternatives = alternatives - set(x)

                        # Then get the suggestions and check if they are
                        # actually corrupted. If so, we have successful noise
                        # and we can move to the next condition
                        suggestions = self.suggestions_provider.suggest_dx(state, action)
                        if will_corrupt:
                            self.assertEqual(min(len(expected_values['dx_suggestions']), self.sm.max_dx_suggestions), len(suggestions))
                            for suggestion in suggestions:
                                self.assertNotIn(suggestion, expected_values['dx_suggestions'])

                            # We correctly predicted noise, and we can move on
                            break

                        else:
                            self._check_suggestions(expected_values['dx_suggestions'][:self.sm.max_dx_suggestions], suggestions, locals())

                    # If we should show action suggestions, then check for noise
                    if self.user.show_ax_suggestions:
                        expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                        valid_actions_check = state.get_valid_actions()
                        alternatives = set([k for k, v in valid_actions_check.items() if (k not in expected_suggestions and v)])


                        # Predict if we will see noise
                        will_corrupt = (self.rng.uniform() < self.user.noise_level)
                        if will_corrupt and idx < len(action_sequence)-1:
                            encountered_noise = True
                            # Move the rng forward
                            x = self.rng.choice(list(alternatives),
                                                size=min(len(expected_suggestions), self.sm.max_ax_suggestions),
                                                replace=False)
                            alternatives = alternatives - set(x)

                        # Then get the suggestions and check if they are
                        # actually corrupted. If so, we have successful noise
                        # and we can move to the next condition
                        suggestions = self.suggestions_provider.suggest_ax(state, action)
                        if will_corrupt:
                            self.assertEqual(min(self.sm.max_ax_suggestions, len(expected_suggestions)), len(suggestions))
                            for suggestion in suggestions:
                                self.assertNotIn(suggestion, expected_suggestions)

                            # We correctly predicted noise, and we can move on
                            break
                        else:
                            self._check_suggestions(expected_suggestions, suggestions, locals())

                # Check that we have encountered noise in this condition
                self.assertTrue(encountered_noise, f"Did not encounter noise in {study_condition}, {start_state_str}")
