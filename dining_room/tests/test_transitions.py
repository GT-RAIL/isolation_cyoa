import os
import collections

from django.test import SimpleTestCase

from dining_room.models import User
from dining_room.views import get_next_state_json


# Create your tests here.


class StateTransitionTestCase(SimpleTestCase):
    """
    Test the state transitions (and only the state transitions)
    """

    def assertTransitionValues(self, expected, actual):
        """Check that the JSON dictionary contains the values in expected, with
        some special conditions depending on the keys that we are checking"""
        for key, value in expected.items():
            # Check that the key exists
            self.assertIn(key, actual)

            # Coerce types, if necessary
            if isinstance(value, (list, tuple,)):
                value = tuple(value)
            if isinstance(actual[key], (list, tuple,)):
                actual[key] = tuple(actual[key])

            # Some keys require a special comparison
            if key == 'video_link':
                self.assertEqual(value, os.path.basename(actual[key]))
            else:
                self.assertEqual(value, actual[key])

    def run_action_sequence(self, start_state_tuple, action_sequence):
        """Run the series of actions specified in action_sequence until the end.
        At the end, make sure that we have indeed ended"""
        state_tuple = start_state_tuple
        for idx, (action, expected_values) in enumerate(action_sequence):
            next_json = get_next_state_json(state_tuple, action)
            expected_values['scenario_completed'] = (idx + 1 == len(action_sequence))

            try:
                self.assertTransitionValues(expected_values, next_json)
            except AssertionError as e:
                print(f"Error in step {idx+1}/{len(action_sequence)}:")
                raise

            state_tuple = next_json['server_state_tuple']

    # First the optimal trajectories through the scenarios

    def test_optimal_AT_COUNTER_ABOVE_MUG(self):
        start_state_tuple = User.StartConditions.AT_COUNTER_ABOVE_MUG.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.kc.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'pick_bowl',
                { 'server_state_tuple': ["kc", "kc", "default", "gripper", "default", "bowl", "dt"],
                  'video_link': 'kc.kc.default.above_mug.default.pick_bowl.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["kc", "kc", "default", "gripper", "default", "empty", "dt"],
                  'video_link': "kc.kc.default.gripper.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["kc", "kc", "default", "gripper", "gripper", "mug", "dt"],
                  "video_link": "kc.kc.default.gripper.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "kc", "default", "gripper", "gripper", "mug", "dt"],
                  'video_link': "kc.kc.default.gripper.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_COUNTER_OCCLUDING(self):
        start_state_tuple = User.StartConditions.AT_COUNTER_OCCLUDING.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.kc.occluding.default.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'pick_jug',
                { 'server_state_tuple': ["kc", "kc", "gripper", "default", "default", "jug", "dt"],
                  'video_link': 'kc.kc.occluding.default.default.pick_jug.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["kc", "kc", "gripper", "default", "default", "empty", "dt"],
                  'video_link': "kc.kc.gripper.default.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["kc", "kc", "gripper", "default", "gripper", "mug", "dt"],
                  "video_link": "kc.kc.gripper.default.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "kc", "gripper", "default", "gripper", "mug", "dt"],
                  'video_link': "kc.kc.gripper.default.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_COUNTER_OCCLUDING_ABOVE_MUG(self):
        start_state_tuple = User.StartConditions.AT_COUNTER_OCCLUDING_ABOVE_MUG.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.kc.occluding.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'pick_jug',
                { 'server_state_tuple': ["kc", "kc", "gripper", "above_mug", "default", "jug", "dt"],
                  'video_link': 'kc.kc.occluding.above_mug.default.pick_jug.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["kc", "kc", "gripper", "above_mug", "default", "empty", "dt"],
                  'video_link': "kc.kc.gripper.above_mug.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_bowl',
                { 'server_state_tuple': ["kc", "kc", "gripper", "gripper", "default", "bowl", "dt"],
                  'video_link': 'kc.kc.gripper.above_mug.default.pick_bowl.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["kc", "kc", "gripper", "gripper", "default", "empty", "dt"],
                  'video_link': "kc.kc.gripper.gripper.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["kc", "kc", "gripper", "gripper", "gripper", "mug", "dt"],
                  "video_link": "kc.kc.gripper.gripper.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "kc", "gripper", "gripper", "gripper", "mug", "dt"],
                  'video_link': "kc.kc.gripper.gripper.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_COUNTER_MISLOCALIZED(self):
        start_state_tuple = User.StartConditions.AT_COUNTER_MISLOCALIZED.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'dt.kc.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'at_dt',
                { 'server_state_tuple': ["dt", "kc", "default", "default", "default", "empty", "dt"],
                  'video_link': 'dt.kc.default.above_mug.default.noop.empty.mp4',
                  'action_result': True, }
            ),
            (
                'go_to_kc',
                { 'server_state_tuple': ["kc", "kc", "default", "default", "default", "empty", "dt"],
                  'video_link': "dt.kc.default.default.default.go_to_kc.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["kc", "kc", "default", "default", "gripper", "mug", "dt"],
                  "video_link": "kc.kc.default.default.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "kc", "default", "default", "gripper", "mug", "dt"],
                  'video_link': "kc.kc.default.default.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_TABLE(self):
        start_state_tuple = User.StartConditions.AT_TABLE.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'go_to_dt',
                { 'server_state_tuple': ["dt", "dt", "default", "default", "default", "empty", "dt"],
                  'video_link': 'kc.dt.default.default.default.go_to_dt.empty.mp4',
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["dt", "dt", "default", "default", "gripper", "mug", "dt"],
                  "video_link": "dt.dt.default.default.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "dt", "default", "default", "gripper", "mug", "dt"],
                  'video_link': "dt.dt.default.default.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_TABLE_ABOVE_MUG(self):
        start_state_tuple = User.StartConditions.AT_TABLE_ABOVE_MUG.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'go_to_dt',
                { 'server_state_tuple': ["dt", "dt", "default", "above_mug", "default", "empty", "dt"],
                  'video_link': 'kc.dt.default.above_mug.default.go_to_dt.empty.mp4',
                  'action_result': True, }
            ),
            (
                'pick_bowl',
                { 'server_state_tuple': ["dt", "dt", "default", "gripper", "default", "bowl", "dt"],
                  'video_link': 'dt.dt.default.above_mug.default.pick_bowl.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["dt", "dt", "default", "gripper", "default", "empty", "dt"],
                  'video_link': "dt.dt.default.gripper.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["dt", "dt", "default", "gripper", "gripper", "mug", "dt"],
                  "video_link": "dt.dt.default.gripper.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "dt", "default", "gripper", "gripper", "mug", "dt"],
                  'video_link': "dt.dt.default.gripper.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_TABLE_OCCLUDING(self):
        start_state_tuple = User.StartConditions.AT_TABLE_OCCLUDING.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'go_to_dt',
                { 'server_state_tuple': ["dt", "dt", "occluding", "default", "default", "empty", "dt"],
                  'video_link': 'kc.dt.occluding.default.default.go_to_dt.empty.mp4',
                  'action_result': True, }
            ),
            (
                'pick_jug',
                { 'server_state_tuple': ["dt", "dt", "gripper", "default", "default", "jug", "dt"],
                  'video_link': 'dt.dt.occluding.default.default.pick_jug.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["dt", "dt", "gripper", "default", "default", "empty", "dt"],
                  'video_link': "dt.dt.gripper.default.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["dt", "dt", "gripper", "default", "gripper", "mug", "dt"],
                  "video_link": "dt.dt.gripper.default.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "dt", "gripper", "default", "gripper", "mug", "dt"],
                  'video_link': "dt.dt.gripper.default.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)

    def test_optimal_AT_TABLE_OCCLUDING_ABOVE_MUG(self):
        start_state_tuple = User.StartConditions.AT_TABLE_OCCLUDING_ABOVE_MUG.value.split('.')
        action_sequence = [
            (
                None,
                { 'server_state_tuple': start_state_tuple,
                  "video_link": 'kc.dt.default.above_mug.default.noop.empty.mp4',
                  "action_result": True, }
            ),
            (
                'go_to_dt',
                { 'server_state_tuple': ["dt", "dt", "occluding", "above_mug", "default", "empty", "dt"],
                  'video_link': 'kc.dt.occluding.above_mug.default.go_to_dt.empty.mp4',
                  'action_result': True, }
            ),
            (
                'pick_jug',
                { 'server_state_tuple': ["dt", "dt", "gripper", "above_mug", "default", "jug", "dt"],
                  'video_link': 'dt.dt.occluding.above_mug.default.pick_jug.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["dt", "dt", "gripper", "above_mug", "default", "empty", "dt"],
                  'video_link': "dt.dt.gripper.above_mug.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_bowl',
                { 'server_state_tuple': ["dt", "dt", "gripper", "gripper", "default", "bowl", "dt"],
                  'video_link': 'dt.dt.gripper.above_mug.default.pick_bowl.empty.mp4',
                  'action_result': True, }
            ),
            (
                'place',
                { 'server_state_tuple': ["dt", "dt", "gripper", "gripper", "default", "empty", "dt"],
                  'video_link': "dt.dt.gripper.gripper.default.place.empty.mp4",
                  'action_result': True, }
            ),
            (
                'pick_mug',
                { 'server_state_tuple': ["dt", "dt", "gripper", "gripper", "gripper", "mug", "dt"],
                  "video_link": "dt.dt.gripper.gripper.default.pick_mug.empty.mp4",
                  'action_result': True }
            ),
            (
                'go_to_c',
                { 'server_state_tuple': ["c", "dt", "gripper", "gripper", "gripper", "mug", "dt"],
                  'video_link': "dt.kc.gripper.gripper.gripper.go_to_c.empty.mp4",
                  'action_result': True }
            ),
        ]
        self.run_action_sequence(start_state_tuple, action_sequence)
