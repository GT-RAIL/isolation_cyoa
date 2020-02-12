import os
import collections

from django.test import SimpleTestCase, TestCase, Client

from dining_room import constants
from dining_room.models import User
from dining_room.models.domain import State, Transition, Suggestions
from dining_room.views import get_next_state_json, get_suggestions_json


# The actual test is here.

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
        # Create a user and log them in
        user = User.objects.create_user('test_user', 'test_user')
        user.study_condition = User.StudyConditions.DXAX_100
        user.start_condition = User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG
        user.save()

        # # Log the user in on the client
        self.client.login(username='test_user', password='test_user')

        self.suggestions_provider = Suggestions(user)

    def test_ordered_diagnoses(self):
        """Test the ordered diagnosis method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                try:
                    state = State(expected_values['server_state_tuple'])

                    # Get the suggestions & test them
                    suggestions = self.suggestions_provider.ordered_diagnoses(state, action, accumulate=True)
                    self.assertListEqual(expected_values['dx_suggestions'], suggestions)

                    suggestions = self.suggestions_provider.ordered_diagnoses(state, action)
                    self.assertListEqual([expected_values['dx_suggestions'][0]], suggestions)

                except AssertionError as e:
                    print(f"Error in {start_state_str} step {idx+1}/{len(action_sequence)}: {e}")
                    raise

    def test_optimal_actions(self):
        """Test the optimal actions method from the Suggestions"""
        for start_state_str, action_sequence in constants.OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                try:
                    state = State(expected_values['server_state_tuple'])

                    # Get the suggestions
                    suggestions = self.suggestions_provider.optimal_actions(state, action)

                    # Test the suggestions
                    if idx == len(action_sequence)-1:
                        self.assertListEqual([], suggestions)
                    else:
                        self.assertListEqual([action_sequence[idx+1][0]], suggestions)

                except AssertionError as e:
                    print(f"Error in {start_state_str} step {idx+1}/{len(action_sequence)}: {e}")
                    raise
