#!/usr/bin/env python
# Various constants that don't make sense elsewhere. Formatted so that we can
# use this information outside docker and without Django

import os
import sys
import copy
import logging
import collections

import numpy as np


# Helper classes

class objdict(dict):
    """Provides class-like access to a dictionary"""
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)


class bijectivedict:
    """Provides a bijective dictionary for lookup by keys and values"""
    MISSING_VALUE = '__MISSING__'

    def __init__(self, *args, **kwargs):
        self.forward = dict(*args, **kwargs)
        self.backward = { v: k for k, v in self.forward.items() }

    def __str__(self):
        return str(self.forward) + str(self.backward)

    def __repr__(self):
        return str(self)

    def __getitem__(self, name):
        if (
            (name not in self.forward or self.forward[name] == bijectivedict.MISSING_VALUE)
            and (name not in self.backward or self.backward[name] == bijectivedict.MISSING_VALUE)
        ):
            raise AttributeError("No such attribute: " + name)

        return self.forward.get(name) or self.backward.get(name)

    def __setitem__(self, name, value):
        assert name != bijectivedict.MISSING_VALUE and value != bijectivedict.MISSING_VALUE, \
            "Cannot add key {}".format(bijectivedict.MISSING_VALUE)

        if name in self.forward:
            if self.forward[name] != bijectivedict.MISSING_VALUE:
                self.backward[self.forward[name]] = bijectivedict.MISSING_VALUE
        if value in self.backward:
            if self.backward[value] != bijectivedict.MISSING_VALUE:
                self.forward[self.backward[value]] = bijectivedict.MISSING_VALUE

        self.forward[name] = value
        self.backward[value] = name

    def __delitem__(self, name):
        if name in self.forward:
            if self.forward[name] != bijectivedict.MISSING_VALUE:
                value = self.forward[name]
                del self.backward[value]
            del self.forward[name]


# The actions that we can handle at any given state
ACTIONS = collections.OrderedDict({
    'at_c': "Update robot's location belief to: Couch",
    'at_dt': "Update robot's location belief to:  Dining Table",
    'at_kc': "Update robot's location belief to:  Kitchen Counter",
    'go_to_c': "Navigate to Couch",
    'go_to_dt': "Navigate to Dining Table",
    'go_to_kc': "Navigate to Kitchen Counter",
    'remove_obstacle': "Remove the obstacle blocking navigation",
    'out_of_collision': "Move away from a collision",
    'look_at_c': "Look at Couch",
    'look_at_dt': "Look at Dining Table",
    'look_at_kc': "Look at Kitchen Counter",
    'pick_bowl': "Pick up the Bowl",
    'pick_jug': "Pick up the Jug",
    'pick_mug': "Pick up the Cup",
    'place': "Put away held object",
    'restart_video': "Restart the camera",
    'find_charger': "Find the charger and navigate to it",
})


# The objects in this scenario
OBJECTS = ['jug', 'bowl', 'mug']


# The locations in this scenario
LOCATIONS = ['kc', 'dt', 'c']


# The mapping of locations to their expanded name
LOCATION_NAMES = bijectivedict({
    'kc': 'kitchen_counter',
    'dt': 'dining_table',
    'c': 'couch',
})


# The mappings of locations based on the mapping of the table
LOCATION_MAPPINGS = {
    'dining_table_to_dining_table': objdict({
        'dining_table': 'dining_table',
        'kitchen_counter': 'kitchen_counter',
        'couch': 'couch',
    }),

    'dining_table_to_kitchen_counter': objdict({
        'dining_table': 'kitchen_counter',
        'kitchen_counter': 'couch',
        'couch': 'dining_table',
    }),

    'dining_table_to_couch': objdict({
        'dining_table': 'couch',
        'kitchen_counter': 'dining_table',
        'couch': 'kitchen_counter',
    }),
}


# Empty gripper
EMPTY_GRIPPER = 'empty'
EMPTY_GRIPPER_DISPLAY = 'nothing'


# Object states
OBJECT_STATES = {
    'jug': ['default', 'occluding', 'gripper'],
    'bowl': ['default', 'above_mug', 'gripper'],
    'mug': ['default', 'gripper'],
}


# The arm statuses
ARM_STATUS = ['not_moving', 'in_motion']


# The diagnosis options. These are keys corresponding to display values
DIAGNOSES = collections.OrderedDict({
    'lost': 'The robot is lost',
    'cannot_move': 'The robot is stuck and cannot move to a location',
    'base_collision': 'The robot has collided with an object',
    'path_blocked': "The robot's path is blocked",
    'cannot_pick': 'The cup cannot be picked up',
    'cannot_see': 'The cup is not visible',
    'different_location': 'The cup is not where it should be',
    'object_fell': "The object fell out of the robot's hand",
    'battery_low': 'The battery is low',
    'video_problem': 'There is a problem with the camera',
    'none': 'There is no problem',
})


# The maximum number of actions that we allow
MAX_NUMBER_OF_ACTIONS = 20


# A dictionary mapping progress states through the study to the allowed
# pages in the event those states are reached. If the user navigates to an
# unallowed page, they are redirected to the first allowed page
STUDY_PROGRESS_STATES = objdict({
    # If the user has been created but hasn't logged in, then redirect to
    # login. This will happen anyway because of login_required
    'CREATED': ['login'],
    # If demographics haven't been completed, redirect to demographics
    'LOGGED_IN': ['demographics'],
    # If the study has not been completed, but demographics have been,
    # then redirect to the instructions or the knowledge test
    'DEMOGRAPHED': ['instructions', 'test', 'study'],
    # If the user has started the study, then they may only be on the study
    # pages
    'STARTED': ['study', 'survey'],
    # If the user has completed the study but not the survey, then redirect
    # them to the survey
    'FINISHED': ['survey'],
    # If the user has completed the study, and the survey, then redirect
    # to the completed page
    'SURVEYED': ['complete'],
    # If the user has failed the knowledge test, then mark them as failed
    'FAILED': ['fail'],
})


# The optimal action sequences for different start conditions
OPTIMAL_ACTION_SEQUENCES = {
    'kc.kc.default.above_mug.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'kc', 'default', 'above_mug', 'default', 'empty', 'dt'],
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

    'kc.kc.occluding.default.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'kc', 'occluding', 'default', 'default', 'empty', 'dt'],
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

    'kc.kc.occluding.above_mug.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'kc', 'occluding', 'above_mug', 'default', 'empty', 'dt'],
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

    'dt.kc.default.default.default.empty.kc': [
        (
            None,
            {
                'server_state_tuple': ['dt', 'kc', 'default', 'default', 'default', 'empty', 'kc'],
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

    'kc.dt.default.default.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'dt', 'default', 'default', 'default', 'empty', 'dt'],
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

    'kc.dt.default.above_mug.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'dt', 'default', 'above_mug', 'default', 'empty', 'dt'],
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

    'kc.dt.occluding.default.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'dt', 'occluding', 'default', 'default', 'empty', 'dt'],
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

    'kc.dt.occluding.above_mug.default.empty.dt': [
        (
            None,
            {
                'server_state_tuple': ['kc', 'dt', 'occluding', 'above_mug', 'default', 'empty', 'dt'],
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
