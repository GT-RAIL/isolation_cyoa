import os
import collections

from django.test import SimpleTestCase

from dining_room.models import User
from dining_room.models.domain import constants, State, Transition, Suggestions
from dining_room.views import get_next_state_json, get_suggestions_json


# Constants

# The optimal action sequences for different start conditions
OPTIMAL_ACTION_SEQUENCES = {
    User.StartConditions.AT_COUNTER_ABOVE_MUG: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_COUNTER_ABOVE_MUG.value.split('.'),
                "video_link": 'kc.kc.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                "dx_suggestions": ['cannot_pick'],
            }
        ),
        (
            'pick_bowl',
            {
                'server_state_tuple': ["kc", "kc", "default", "gripper", "default", "bowl", "dt"],
                'video_link': 'kc.kc.default.above_mug.default.pick_bowl.empty.mp4',
                'action_result': True,
                "dx_suggestions": ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["kc", "kc", "default", "gripper", "default", "empty", "dt"],
                'video_link': "kc.kc.default.gripper.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["kc", "kc", "default", "gripper", "gripper", "mug", "dt"],
                "video_link": "kc.kc.default.gripper.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "kc", "default", "gripper", "gripper", "mug", "dt"],
                'video_link': "kc.kc.default.gripper.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_COUNTER_OCCLUDING: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_COUNTER_OCCLUDING.value.split('.'),
                "video_link": 'kc.kc.occluding.default.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['cannot_see', 'cannot_pick'],
            }
        ),
        (
            'pick_jug',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "default", "default", "jug", "dt"],
                'video_link': 'kc.kc.occluding.default.default.pick_jug.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "default", "default", "empty", "dt"],
                'video_link': "kc.kc.gripper.default.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "default", "gripper", "mug", "dt"],
                "video_link": "kc.kc.gripper.default.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "kc", "gripper", "default", "gripper", "mug", "dt"],
                'video_link': "kc.kc.gripper.default.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG.value.split('.'),
                "video_link": 'kc.kc.occluding.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['cannot_see', 'cannot_pick'],
            }
        ),
        (
            'pick_jug',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "above_mug", "default", "jug", "dt"],
                'video_link': 'kc.kc.occluding.above_mug.default.pick_jug.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_pick'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "above_mug", "default", "empty", "dt"],
                'video_link': "kc.kc.gripper.above_mug.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['cannot_pick'],
            }
        ),
        (
            'pick_bowl',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "gripper", "default", "bowl", "dt"],
                'video_link': 'kc.kc.gripper.above_mug.default.pick_bowl.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "gripper", "default", "empty", "dt"],
                'video_link': "kc.kc.gripper.gripper.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["kc", "kc", "gripper", "gripper", "gripper", "mug", "dt"],
                "video_link": "kc.kc.gripper.gripper.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "kc", "gripper", "gripper", "gripper", "mug", "dt"],
                'video_link': "kc.kc.gripper.gripper.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_COUNTER_MISLOCALIZED: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_COUNTER_MISLOCALIZED.value.split('.'),
                "video_link": 'dt.kc.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['lost', 'cannot_see', 'cannot_pick'],
            }
        ),
        (
            'at_dt',
            {
                'server_state_tuple': ["dt", "kc", "default", "default", "default", "empty", "dt"],
                'video_link': 'dt.kc.default.above_mug.default.noop.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_see', 'cannot_pick'],
            }
        ),
        (
            'go_to_kc',
            {
                'server_state_tuple': ["kc", "kc", "default", "default", "default", "empty", "dt"],
                'video_link': "dt.kc.default.default.default.go_to_kc.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["kc", "kc", "default", "default", "gripper", "mug", "dt"],
                "video_link": "kc.kc.default.default.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "kc", "default", "default", "gripper", "mug", "dt"],
                'video_link': "kc.kc.default.default.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_TABLE: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_TABLE.value.split('.'),
                "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['different_location', 'cannot_see', 'cannot_pick'],
            }
        ),
        (
            'go_to_dt',
            {
                'server_state_tuple': ["dt", "dt", "default", "default", "default", "empty", "dt"],
                'video_link': 'kc.dt.default.default.default.go_to_dt.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["dt", "dt", "default", "default", "gripper", "mug", "dt"],
                "video_link": "dt.dt.default.default.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "dt", "default", "default", "gripper", "mug", "dt"],
                'video_link': "dt.dt.default.default.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_TABLE_ABOVE_MUG: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_TABLE_ABOVE_MUG.value.split('.'),
                "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['different_location', 'cannot_see', 'cannot_pick'],
            }
        ),
        (
            'go_to_dt',
            {
                'server_state_tuple': ["dt", "dt", "default", "above_mug", "default", "empty", "dt"],
                'video_link': 'kc.dt.default.above_mug.default.go_to_dt.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_pick'],
            }
        ),
        (
            'pick_bowl',
            {
                'server_state_tuple': ["dt", "dt", "default", "gripper", "default", "bowl", "dt"],
                'video_link': 'dt.dt.default.above_mug.default.pick_bowl.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["dt", "dt", "default", "gripper", "default", "empty", "dt"],
                'video_link': "dt.dt.default.gripper.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["dt", "dt", "default", "gripper", "gripper", "mug", "dt"],
                "video_link": "dt.dt.default.gripper.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "dt", "default", "gripper", "gripper", "mug", "dt"],
                'video_link': "dt.dt.default.gripper.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_TABLE_OCCLUDING: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_TABLE_OCCLUDING.value.split('.'),
                "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['different_location', 'cannot_see', 'cannot_pick'],
            }
        ),
        (
            'go_to_dt',
            {
                'server_state_tuple': ["dt", "dt", "occluding", "default", "default", "empty", "dt"],
                'video_link': 'kc.dt.occluding.default.default.go_to_dt.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_see', 'cannot_pick'],
            }
        ),
        (
            'pick_jug',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "default", "default", "jug", "dt"],
                'video_link': 'dt.dt.occluding.default.default.pick_jug.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "default", "default", "empty", "dt"],
                'video_link': "dt.dt.gripper.default.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "default", "gripper", "mug", "dt"],
                "video_link": "dt.dt.gripper.default.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "dt", "gripper", "default", "gripper", "mug", "dt"],
                'video_link': "dt.dt.gripper.default.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],

    User.StartConditions.AT_TABLE_OCCLUDING_ABOVE_MUG: [
        (
            None,
            {
                'server_state_tuple': User.StartConditions.AT_TABLE_OCCLUDING_ABOVE_MUG.value.split('.'),
                "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                "action_result": True,
                'dx_suggestions': ['different_location', 'cannot_see', 'cannot_pick'],
            }
        ),
        (
            'go_to_dt',
            {
                'server_state_tuple': ["dt", "dt", "occluding", "above_mug", "default", "empty", "dt"],
                'video_link': 'kc.dt.occluding.above_mug.default.go_to_dt.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_see', 'cannot_pick'],
            }
        ),
        (
            'pick_jug',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "above_mug", "default", "jug", "dt"],
                'video_link': 'dt.dt.occluding.above_mug.default.pick_jug.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['cannot_pick'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "above_mug", "default", "empty", "dt"],
                'video_link': "dt.dt.gripper.above_mug.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['cannot_pick'],
            }
        ),
        (
            'pick_bowl',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "gripper", "default", "bowl", "dt"],
                'video_link': 'dt.dt.gripper.above_mug.default.pick_bowl.empty.mp4',
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'place',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "gripper", "default", "empty", "dt"],
                'video_link': "dt.dt.gripper.gripper.default.place.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'pick_mug',
            {
                'server_state_tuple': ["dt", "dt", "gripper", "gripper", "gripper", "mug", "dt"],
                "video_link": "dt.dt.gripper.gripper.default.pick_mug.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
        (
            'go_to_c',
            {
                'server_state_tuple': ["c", "dt", "gripper", "gripper", "gripper", "mug", "dt"],
                'video_link': "dt.kc.gripper.gripper.gripper.go_to_c.empty.mp4",
                'action_result': True,
                'dx_suggestions': ['none'],
            }
        ),
    ],
}


# The actual test is here.

class TransitionTestCase(SimpleTestCase):
    """
    Test:
    1. the state transitions given sequences of actions
    2. the diagnoses and actions given states and actions
    """

    # For testing action sequences

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
        for start_state, action_sequence in OPTIMAL_ACTION_SEQUENCES.items():
            start_state_tuple = start_state.value.split('.')
            self._run_test_action_sequence(start_state_tuple, action_sequence)

    # For testing suggestions
    def test_ordered_diagnoses(self):
        """Test the ordered diagnosis method from the Suggestions"""
        suggestions_provider = Suggestions(None)
        for start_state, action_sequence in OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                try:
                    state = State(expected_values['server_state_tuple'])

                    # Get the suggestions & test them
                    suggestions = suggestions_provider.ordered_diagnoses(state, action, accumulate=True)
                    self.assertListEqual(expected_values['dx_suggestions'], suggestions)

                    suggestions = suggestions_provider.ordered_diagnoses(state, action)
                    self.assertListEqual([expected_values['dx_suggestions'][0]], suggestions)

                except AssertionError as e:
                    print(f"Error in {start_state} step {idx+1}/{len(action_sequence)}: {e}")
                    raise

    def test_optimal_actions(self):
        """Test the optimal actions method from the Suggestions"""
        suggestions_provider = Suggestions(None)
        for start_state, action_sequence in OPTIMAL_ACTION_SEQUENCES.items():
            for idx, (action, expected_values) in enumerate(action_sequence):
                try:
                    state = State(expected_values['server_state_tuple'])

                    # Get the suggestions
                    suggestions = suggestions_provider.optimal_actions(state, action)

                    # Test the suggestions
                    if idx == len(action_sequence)-1:
                        self.assertListEqual([], suggestions)
                    else:
                        self.assertListEqual([action_sequence[idx+1][0]], suggestions)

                except AssertionError as e:
                    print(f"Error in {start_state} step {idx+1}/{len(action_sequence)}: {e}")
                    raise
