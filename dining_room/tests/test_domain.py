import os
import copy
import collections
import unittest

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

    def _reset_rng(self, idx):
        """
        If idx = 0, reset the RNG to default. Else user the users' value. This
        refreshes the RNG values in the provider to simulate how we expect
        the RNG values to evolve as user requests come in
        """
        self.user.refresh_from_db()
        if idx == 0:
            self.user.rng_state = Suggestions.DEFAULT_RNG_SEED
            self.user.save()
            self.suggestions_provider = Suggestions(self.user)
            self.rng = np.random.default_rng(Suggestions.DEFAULT_RNG_SEED)
        else:
            self.suggestions_provider = Suggestions(self.user)
            self.rng = np.random.default_rng(self.user.rng_state)

    def test_ordered_diagnoses(self):
        """Test the ordered diagnosis method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = expected_values['dx_suggestions']

                # Get the suggestions & test them
                suggestions = self.suggestions_provider.ordered_diagnoses(state, action, accumulate=True)
                self.assertListEqual(expected_suggestions, suggestions)

                suggestions = self.suggestions_provider.ordered_diagnoses(state, action)
                self.assertListEqual([expected_suggestions[0]], suggestions)

    def test_optimal_action(self):
        """Test the optimal actions method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]

                # Get the suggestions
                suggestions = self.suggestions_provider.optimal_action(state, action)

                # Test the suggestions
                self.assertListEqual(expected_suggestions, suggestions)

    def test_should_corrupt_3(self):
        """
        Test that the suggestions will get corrupted when we want them to be.
        Level 3 noise
        """
        dx_pattern = [False, True, False, False, True, False, False, False, True, False,
                      False, True, False, False, True, False, False, False, True, False]
        ax_pattern = [False, True, False, False, False, True, False, True, False, False,
                      False, True, False, False, False, True, False, True, False, False]

        self.user.study_condition = User.StudyConditions.DXAX_70
        self.user.save()
        self.suggestions_provider = Suggestions(self.user)

        generated_dx = []
        generated_ax = []
        for action_idx in range(20):
            self.user.refresh_from_db()
            self.user.number_state_requests += 1
            self.user.save()

            generated_dx.append(self.suggestions_provider._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS))
            generated_ax.append(self.suggestions_provider._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS))

        self.assertListEqual(dx_pattern, generated_dx)
        self.assertListEqual(ax_pattern, generated_ax)

    def test_should_corrupt_2(self):
        """
        Test that the suggestions will get corrupted when we want them to be.
        Level 2 noise
        """
        dx_pattern = [False, True, False, False, True, False, False, False, False, False,
                      False, True, False, False, True, False, False, False, False, False]
        ax_pattern = [False, True, False, False, False, True, False, False, False, False,
                      False, True, False, False, False, True, False, False, False, False]

        self.user.study_condition = User.StudyConditions.DXAX_80
        self.user.save()
        self.suggestions_provider = Suggestions(self.user)

        generated_dx = []
        generated_ax = []
        for action_idx in range(20):
            self.user.refresh_from_db()
            self.user.number_state_requests += 1
            self.user.save()

            generated_dx.append(self.suggestions_provider._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS))
            generated_ax.append(self.suggestions_provider._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS))

        self.assertListEqual(dx_pattern, generated_dx)
        self.assertListEqual(ax_pattern, generated_ax)

    def test_should_corrupt_1(self):
        """
        Test that the suggestions will get corrupted when we want them to be.
        Level 1 noise
        """
        dx_pattern = [False, True, False, False, False, False, False, False, False, False,
                      False, True, False, False, False, False, False, False, False, False]
        ax_pattern = [False, True, False, False, False, False, False, False, False, False,
                      False, True, False, False, False, False, False, False, False, False]

        self.user.study_condition = User.StudyConditions.DXAX_90
        self.user.save()
        self.suggestions_provider = Suggestions(self.user)

        generated_dx = []
        generated_ax = []
        for action_idx in range(20):
            self.user.refresh_from_db()
            self.user.number_state_requests += 1
            self.user.save()

            generated_dx.append(self.suggestions_provider._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS))
            generated_ax.append(self.suggestions_provider._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS))

        self.assertListEqual(dx_pattern, generated_dx)
        self.assertListEqual(ax_pattern, generated_ax)

    def test_should_corrupt_0(self):
        """
        Test that the suggestions will get corrupted when we want them to be.
        Level 0 noise
        """
        dx_pattern = [False, False, False, False, False, False, False, False, False, False,
                      False, False, False, False, False, False, False, False, False, False]
        ax_pattern = [False, False, False, False, False, False, False, False, False, False,
                      False, False, False, False, False, False, False, False, False, False]

        self.user.study_condition = User.StudyConditions.DXAX_100
        self.user.save()
        self.suggestions_provider = Suggestions(self.user)

        generated_dx = []
        generated_ax = []
        for action_idx in range(20):
            self.user.refresh_from_db()
            self.user.number_state_requests += 1
            self.user.save()

            generated_dx.append(self.suggestions_provider._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS))
            generated_ax.append(self.suggestions_provider._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS))

        self.assertListEqual(dx_pattern, generated_dx)
        self.assertListEqual(ax_pattern, generated_ax)

    def _test_dx_suggestions(self, state, action, expected_suggestions, pad):
        """Given state, action, and expected suggestions, test the suggestions"""
        alternatives = [x for x in constants.DIAGNOSES.keys() if x not in expected_suggestions]
        expected_suggestions = expected_suggestions[:self.sm.max_dx_suggestions]

        # Predict if we will see noise & then add noise accordingly
        will_corrupt = self.suggestions_provider._should_corrupt(Suggestions.DX_CORRUPT_IDX_OFFSETS)
        if will_corrupt:
            # Move the rng forward
            padded_suggestions = self.rng.choice(alternatives, size=len(expected_suggestions), replace=False).tolist()
        else:
            padded_suggestions = [x for x in expected_suggestions]

        # Then update if we need to pad
        if pad:
            alternatives = set(alternatives) - set(padded_suggestions)
            for _ in range(len(expected_suggestions), self.sm.max_dx_suggestions):
                padded_suggestions.append(self.rng.choice(list(sorted(alternatives))))
                alternatives.discard(padded_suggestions[-1])

        # Then get the suggestions & check if they match. Add additional checks
        # if they are corrupted
        suggestions = self.suggestions_provider.suggest_dx(state, action)
        self.assertGreaterEqual(self.sm.max_dx_suggestions, len(suggestions))

        # The first test
        if pad:
            self.assertEqual(self.sm.max_dx_suggestions, len(suggestions))
        else:
            self.assertEqual(len(expected_suggestions), len(suggestions))

        # The second test
        for idx, suggestion in enumerate(expected_suggestions):
            if will_corrupt:
                self.assertNotIn(suggestion, suggestions)
            else:
                self.assertIn(suggestion, suggestions)

        # The final test... Do we predict the padded values well?
        self.assertListEqual(padded_suggestions, suggestions)

        # Return the suggestions, the padded suggestions
        return suggestions, padded_suggestions, will_corrupt

    def _test_ax_suggestions(self, state, action, expected_suggestions, pad):
        """Given state, action, and expected suggestions, test the suggestions"""
        valid_actions_check = state.get_valid_actions()
        alternatives = [k for k, v in valid_actions_check.items() if (k not in expected_suggestions and v)]
        expected_suggestions = expected_suggestions[:self.sm.max_ax_suggestions]

        # Predict if we will see noise & then add noise accordingly
        will_corrupt = self.suggestions_provider._should_corrupt(Suggestions.AX_CORRUPT_IDX_OFFSETS)
        if will_corrupt:
            # Move the rng forward
            padded_suggestions = self.rng.choice(alternatives, size=len(expected_suggestions), replace=False).tolist()
        else:
            padded_suggestions = [x for x in expected_suggestions]

        # Then update if we need to pad
        if pad:
            alternatives = set(alternatives) - set(padded_suggestions)
            for _ in range(len(expected_suggestions), self.sm.max_ax_suggestions):
                padded_suggestions.append(self.rng.choice(list(sorted(alternatives))))
                alternatives.discard(padded_suggestions[-1])

        # Then get the suggestions & check if they match. Add additional checks
        # if they are corrupted
        suggestions = self.suggestions_provider.suggest_ax(state, action)
        self.assertGreaterEqual(self.sm.max_ax_suggestions, len(suggestions))

        # The first test
        if pad:
            self.assertEqual(self.sm.max_ax_suggestions, len(suggestions))
        else:
            self.assertEqual(len(expected_suggestions), len(suggestions))

        # The second test
        for idx, suggestion in enumerate(expected_suggestions):
            if will_corrupt:
                self.assertNotIn(suggestion, suggestions)
            else:
                self.assertIn(suggestion, suggestions)

        # The final test... Do we predict the padded values well?
        self.assertListEqual(padded_suggestions, suggestions)

        # Return the suggestions, the padded suggestions
        return suggestions, padded_suggestions, will_corrupt

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

                expected_suggestions = expected_values['dx_suggestions']
                _, _, will_corrupt = self._test_dx_suggestions(state, action, expected_suggestions, pad=False)
                self.assertFalse(will_corrupt)

                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                _, _, will_corrupt = self._test_ax_suggestions(state, action, expected_suggestions, pad=False)
                self.assertFalse(will_corrupt)

    def test_noisy_dx_suggestions_no_padding(self):
        """Test the addition of noise to the DX suggestions, without adding
        padding"""
        self.user.study_condition = User.StudyConditions.DXAX_70
        self.user.save()
        self.assertEqual(0.3, self.user.noise_level)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                self.user.number_state_requests += 1
                self.user.save()

                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = expected_values['dx_suggestions']

                self._test_dx_suggestions(state, action, expected_suggestions, pad=False)

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

    def test_noisy_ax_suggestions_no_padding(self):
        """Test the addition of noise to the AX suggestions, without adding
        padding"""
        self.user.study_condition = User.StudyConditions.DXAX_70
        self.user.save()
        self.assertEqual(0.3, self.user.noise_level)

        # Refresh the values in the provider
        self.suggestions_provider = Suggestions(self.user)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                self.user.number_state_requests += 1
                self.user.save()

                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]

                self._test_ax_suggestions(state, action, expected_suggestions, pad=False)

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

                expected_suggestions = expected_values['dx_suggestions']
                suggestions, _, will_corrupt = self._test_dx_suggestions(state, action, expected_suggestions, pad=True)
                self.assertFalse(will_corrupt)
                self.assertEqual(self.sm.max_dx_suggestions, len(suggestions))

                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                suggestions, _, will_corrupt = self._test_ax_suggestions(state, action, expected_suggestions, pad=True)
                self.assertFalse(will_corrupt)
                self.assertEqual(self.sm.max_ax_suggestions, len(suggestions))

    def test_multiple_with_noise_and_padding(self):
        """Test multiple suggestions with padding and noise"""
        self.sm.max_dx_suggestions = 3
        self.sm.max_ax_suggestions = 4
        self.sm.pad_suggestions = True
        self.sm.save()

        self.user.study_condition = User.StudyConditions.DXAX_70
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(0.3, self.user.noise_level)

        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                self.user.number_state_requests += 1
                self.user.save()

                self._reset_rng(idx)
                state = State(expected_values['server_state_tuple'])

                # First we do the DX
                expected_suggestions = expected_values['dx_suggestions']

                self._test_dx_suggestions(state, action, expected_suggestions, pad=True)

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

                # Then we do the AX
                expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]

                self._test_ax_suggestions(state, action, expected_suggestions, pad=True)

                # Check the rng state
                self.user.refresh_from_db()
                self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

    def test_all_noise_conditions_see_noise(self):
        """Test that all the noise conditions actually do see noise in the first
        3 actions"""
        action_number_check_threshold = 3

        # Make sure we're running the same condition that we will have for the
        # study. This is where we went wrong last time
        self.sm.max_dx_suggestions = 3
        self.sm.max_ax_suggestions = 3
        self.sm.pad_suggestions = True
        self.sm.save()

        # Iterate through the study conditions
        for study_condition in [User.StudyConditions.DX_90, User.StudyConditions.AX_90, User.StudyConditions.DXAX_90]:
            self.user.study_condition = study_condition
            self.user.save()

            # Then run the same rigamarole of going testing noise without
            # padding
            for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
                encountered_noise = False
                self.user.number_state_requests = -1
                self.user.save()

                # There has to be some noise before the end of the optimal
                # action sequence
                for idx, (action, expected_values) in enumerate(action_sequence[:-1]):
                    self.user.number_state_requests += 1
                    self.user.save()

                    self._reset_rng(idx)

                    state = State(expected_values['server_state_tuple'])

                    # If DX should be shown, then calculate the noise probabilty
                    if self.user.show_dx_suggestions:
                        expected_suggestions = expected_values['dx_suggestions']
                        suggestions, _, will_corrupt = self._test_dx_suggestions(state, action, expected_suggestions, pad=True)
                        encountered_noise = encountered_noise or (will_corrupt and idx < action_number_check_threshold)

                    # If we should show action suggestions, then check for noise
                    if self.user.show_ax_suggestions:
                        expected_suggestions = [] if idx == len(action_sequence)-1 else [action_sequence[idx+1][0]]
                        suggestions, _, will_corrupt = self._test_ax_suggestions(state, action, expected_suggestions, pad=True)
                        encountered_noise = encountered_noise or (will_corrupt and idx < action_number_check_threshold)

                    # Check the rng state
                    self.user.refresh_from_db()
                    self.assertEqual(Suggestions.get_next_rng_seed(self.rng), self.user.rng_state)

                # Check that we have encountered noise in this condition
                self.assertTrue(encountered_noise, f"Did not encounter noise in {study_condition}, {start_state_str}")
