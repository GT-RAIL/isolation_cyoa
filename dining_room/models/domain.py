#!/usr/bin/env python
# The file to handle CYOA in the Dining Room domain (described in `tw` and in
# the Overview slides)

import os
import sys
import copy

import numpy as np


"""
Notes:

- If the object location does not match the base location, then the robot
    should not report that anything is visible
- Depending on the condition, the visibility of the robot changes. The bowl and
    jug are not visible when they have been removed. The mug
    is not visible if the jug is occluding (it is visible when the bowl is above
    it though)
- The pick action should not be available until locations coincide
- Pick jug is available unless the jug has been removed, pick bowl is available
    unless the Jug is occluding and the bowl is above the mug. Pick Mug is only
    available if the other two objects are in default or gripper positions
- The place action should not be available until the robot has picked something.
    It is never available in the case of the mug
- The robot should report gripper empty until a pick occurs.
- The videos for picking a non-mug and moving are the same as those for moving
    around after the object has been 'placed'.
- The gripper should be reported as empty if a place happens after a pick; else
    there is something in the gripper
- During pick or place videos, mark the robot's arm as moving, else mark it as
    still
- Relocalization simply updates the names of all the associated locations in the
    state. There (I think) needs to be no other special logic. The video for a
    relocalization action is the no-op video
- At location X, go to Y, Z and look at Y, Z are available. In terms of videos,
    at the kitchen counter, look at dining table serves as the de-facto for both
    look at the couch and look at the table; similarly, look at kitchen counter
    at the couch serves as the de-facto for both looking at the kitchen counter
    and the dining table
- Reuse videos for conditions that have base positions that don't look at
    objects. They are:
    - noop for couch (there is only 1)
    - noop for dining table when objects are on the kitchen counter unless mug
        is in the gripper
    - noop for kitchen counter when objects are on the dining table unless mug
        is in the gripper
    - looking at couch from dining table when objects are on the kitchen counter
        unless mug is in the gripper
    - going to the couch from the dining table when objects are on the kitchen
        counter unless mug is in the gripper
    - going to the dining table from the couch when objects are on the kitchen
        counter
    - going to the couch from the kitchen counter when objects are on the dining
        table unless mug is in the gripper (verify this!)

Ideally, the state should dynamically determine the sets of actions available,
the text to show, and the video to display
"""

# Helper functions and classes

# Included here because we might need to use this module as a standalone in a
# docker container on the webserver

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


def display(string):
    """Given a location or object or action string, get the display name"""
    return " ".join([x.capitalize() for x in string.split('_')])


# Constants for the domain
constants = objdict({
    # The actions that we can handle at any given state
    'ACTIONS': {
        'at_c': "Update robot's location belief to: Couch",
        'at_dt': "Update robot's location belief to:  Dining Table",
        'at_kc': "Update robot's location belief to:  Kitchen Counter",
        'go_to_c': "Navigate to Couch",
        'go_to_dt': "Navigate to Dining Table",
        'go_to_kc': "Navigate to Kitchen Counter",
        'look_at_c': "Look at Couch",
        'look_at_dt': "Look at Dining Table",
        'look_at_kc': "Look at Kitchen Counter",
        'pick_bowl': "Pick up the Bowl",
        'pick_jug': "Pick up the Jug",
        'pick_mug': "Pick up the Cup",
        'place': "Stow object in gripper",
    },

    # The objects in this scenario
    'OBJECTS': ['jug', 'bowl', 'mug'],

    # The locations in this scenario
    'LOCATIONS': ['kc', 'dt', 'c'],

    # The mapping of locations to their expanded name
    'LOCATION_NAMES': bijectivedict({
        'kc': 'kitchen_counter',
        'dt': 'dining_table',
        'c': 'couch',
    }),

    # The mappings of locations based on the mapping of the table
    'LOCATION_MAPPINGS': {
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
    },

    # Empty gripper
    'EMPTY_GRIPPER': 'empty',

    # Object states
    'OBJECT_STATES': {
        'jug': ['default', 'occluding', 'gripper'],
        'bowl': ['default', 'above_mug', 'gripper'],
        'mug': ['default', 'gripper'],
    },

    # The arm statuses
    'ARM_STATUS': ['not_moving', 'in_motion'],

    # The diagnosis options. These are keys corresponding to display values
    'DIAGNOSES': {
        'lost': 'The robot is lost',
        'cannot_pick': 'The cup cannot be picked up',
        'cannot_see': 'The cup is not visible',
        'different_location': 'The cup is not where it should be',
        'none': 'There is no error',
    },

    # The maximum number of actions that we allow
    'MAX_NUMBER_OF_ACTIONS': 20,

    # A dictionary mapping progress states through the study to the allowed
    # pages in the event those states are reached
    'STUDY_PROGRESS_STATES': objdict({
        # If demographics haven't been completed, redirect to demographics
        'CREATED': ['demographics'],
        # If the study has not been completed, but demographics have been,
        # then redirect to the instructions and restart the study
        'DEMOGRAPHED': ['instructions', 'test', 'study', 'survey'],
        # If the user has completed the study, and the survey, then redirect
        # to the completed page
        'SURVEYED': ['complete'],
    }),
})


# The main classes

class State:
    """
    Encapsulates the state of the scenario with the following attributes:

        - the location of the robot base (true location) - kc (default), dt, c
        - the location of the objects (true location) - kc (expected default), dt
        - the state of the jug - default, occluding, gripper (out of view)
        - the state of the bowl - default, above_mug, gripper (out of view)
        - the state of the mug - default, gripper (in view)
        - object in the gripper - empty, jug, bowl, mug
        - the current label for the dining table - dt (default), kc (induced), c

    Based on these attributes, other attributes can be inferred (using methods
    and dynamic properties). These include:

        - the label of the current location
        - the objects that the robot "sees"
        - the actions that the robot can take (IMPORTANT). This is returned as
            the set of ``Transition`` that are applicable at the given state

    In the UI, the ``State`` determines:

        - the text the user sees after a video has played
        - the transitions that the user can make based on helpers from
            ``Transition``. These will be presented as actions to the user
        - if the user is done with the session

    Once a state is initialized, subsequent states are dynamically created.
    """

    # Attributes (private). Use getters and setters instead
    _base_location = None
    _object_location = None
    _jug_state = None
    _bowl_state = None
    _mug_state = None
    _gripper_state = None
    _current_dt_label = None

    def __init__(self, state):
        """
        Given a 7 tuple of the state, create a State object
        """
        if isinstance(state, (list, tuple,)):
            assert len(state) == 7
            self.tuple = state
        elif isinstance(state, State):
            self.tuple = state.tuple
        else:
            raise NotImplementedError("Unknown type: {}".format(state))

    def __eq__(self, other):
        return isinstance(other, State) and (self.tuple == other.tuple)

    def __ne__(self, other):
        if not isinstance(other, State):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __hash__(self):
        return hash(self.tuple)

    def __str__(self):
        return str((
            constants.LOCATION_NAMES[self.base_location],
            constants.LOCATION_NAMES[self.object_location],
            self.jug_state,
            self.bowl_state,
            self.mug_state,
            self.gripper_state,
            self.relocalized_base_location,
        ))

    def __repr__(self):
        return str(self.tuple)

    # Attributes
    @property
    def base_location(self):
        """The true location of the robot base"""
        return self._base_location

    @base_location.setter
    def base_location(self, value):
        assert value in constants.LOCATIONS
        self._base_location = value

    @property
    def object_location(self):
        """The true location of the objects"""
        return self._object_location

    @object_location.setter
    def object_location(self, value):
        assert value in constants.LOCATIONS[:-1]
        self._object_location = value

    @property
    def jug_state(self):
        """The state of the jug"""
        return self._jug_state

    @jug_state.setter
    def jug_state(self, value):
        assert value in constants.OBJECT_STATES['jug']
        self._jug_state = value

    @property
    def bowl_state(self):
        """The state of the bowl"""
        return self._bowl_state

    @bowl_state.setter
    def bowl_state(self, value):
        assert value in constants.OBJECT_STATES['bowl']
        self._bowl_state = value

    @property
    def mug_state(self):
        """The state of the mug"""
        return self._mug_state

    @mug_state.setter
    def mug_state(self, value):
        assert value in constants.OBJECT_STATES['mug']
        self._mug_state = value

    @property
    def gripper_state(self):
        """The state of the gripper"""
        return self._gripper_state

    @gripper_state.setter
    def gripper_state(self, value):
        assert value is None or value in constants.OBJECTS + [constants.EMPTY_GRIPPER]
        self._gripper_state = value or constants.EMPTY_GRIPPER

    @property
    def current_dt_label(self):
        """
        The current mapping of the dining table; used to look up localization
        """
        return self._current_dt_label

    @current_dt_label.setter
    def current_dt_label(self, value):
        assert value in constants.LOCATIONS
        self._current_dt_label = value

    # Inferred attributes
    @property
    def tuple(self):
        """A tuple representation of the state"""
        return (
            self.base_location,
            self.object_location,
            self.jug_state,
            self.bowl_state,
            self.mug_state,
            self.gripper_state,
            self.current_dt_label,
        )

    @tuple.setter
    def tuple(self, value):
        assert len(value) == len(self.tuple)
        self.base_location, self.object_location, self.jug_state, self.bowl_state, self.mug_state, self.gripper_state, self.current_dt_label = value

    @property
    def relocalized_base_location(self):
        """The label of the robot's current location"""
        current_location = constants.LOCATION_NAMES[self.base_location]
        dt_mapping = constants.LOCATION_NAMES[self.current_dt_label]
        relocalized_base_location = constants.LOCATION_MAPPINGS['dining_table_to_' + dt_mapping][current_location]
        return relocalized_base_location

    @property
    def gripper_empty(self):
        """Is the robot's gripper empty?"""
        return self.gripper_state == constants.EMPTY_GRIPPER

    @property
    def visible_objects(self):
        """The objects that are 'visible' to the robot"""
        visible_objects = []
        if self.base_location == self.object_location:
            if self.jug_state != 'gripper':
                visible_objects.append('jug')

            if self.bowl_state != 'gripper' and not (self.jug_state == 'occluding' and self.bowl_state == 'above_mug'):
                visible_objects.append('bowl')

            if self.mug_state == 'default' and self.jug_state != 'occluding':
                visible_objects.append('mug')

        return visible_objects

    @property
    def graspable_objects(self):
        """The objects that the robot can pick up given the state"""
        graspable_objects = []
        if self.gripper_empty and self.base_location == self.object_location:
            # Cache the visible objects
            visible_objects = self.visible_objects

            if 'jug' in visible_objects:
                graspable_objects.append('jug')

            if 'bowl' in visible_objects:
                graspable_objects.append('bowl')

            if 'mug' in visible_objects and self.bowl_state != 'above_mug':
                graspable_objects.append('mug')

        return graspable_objects

    @property
    def is_end_state(self):
        """Return True if this is an end state; else return False"""
        return (
            self.base_location == 'c'
            and self.mug_state == 'gripper'
            and self.gripper_state == 'mug'
            and self.current_dt_label == 'dt'
        )

    # Methods on states
    def get_valid_transitions(self):
        """
        Should be called at most once when the state is first created to get the
        list of potential next states. The returned values, if saved to a
        dictionary can be reused to dynamically grow a state transition graph
        """
        valid_transitions = {}  # Keyed by the actions. Values are next states

        # Iterate through the actions and add to the transitions dictionary if
        # the action is applicable
        for action in constants.ACTIONS.keys():
            end_state = Transition.get_end_state(self, action)
            if end_state is not None:
                valid_transitions[action] = end_state

        # Return the computed transitions
        return valid_transitions


class Transition:
    """
    Encapsulates a move from one state to another using an action. It has the
    following attributes:

        - the start state
        - the action name
        - the resulting state

    From these attributes, other inferred attributes & methods are:

        - the name of the video corresponding to the transition
        - whether the arm is in motion during the transition
        - checking the validity of a possible transition

    In the UI, the ``Transition`` determines:

        - the video that is played when the user selects an action
        - the text that is displayed during the transition (arm motion...?)

    Once a state is provided, we create valid transitions automatically &
    dynamically from that state using methods in the `State` class
    """

    _start_state = None
    _action = None
    _end_state = None

    def __init__(self, start_state, action, end_state):
        self.start_state = start_state
        self.action = action
        self.end_state = end_state

    def __eq__(self, other):
        return isinstance(other, Transition) and (self.tuple == other.tuple)

    def __ne__(self, other):
        if not isinstance(other, Transition):
            return NotImplemented
        else:
            return not self.__eq__(other)

    def __hash__(self):
        return hash(self.tuple)

    def __str__(self):
        return str((self.start_state, constants.ACTIONS.get(self.action, self.action), self.end_state))

    def __repr__(self):
        return repr(self.tuple)

    # Attributes
    @property
    def start_state(self):
        """The state that this transition starts at. None if this is the start"""
        return self._start_state

    @start_state.setter
    def start_state(self, value):
        assert isinstance(value, State) or value is None
        self._start_state = value

    @property
    def action(self):
        """The label of the action"""
        return self._action

    @action.setter
    def action(self, value):
        assert value in constants.ACTIONS.keys() or value is None
        self._action = value

    @property
    def end_state(self):
        """The end state of the transition"""
        return self._end_state

    @end_state.setter
    def end_state(self, value):
        assert isinstance(value, State)
        self._end_state = value

    # Inferred attributes
    @property
    def tuple(self):
        """A tuple representation of the transition"""
        return (
            self.start_state.tuple if self.start_state is not None else None,
            self.action,
            self.end_state.tuple,
        )

    @property
    def arm_status(self):
        """Return if the arm is in motion or not"""
        return constants.ARM_STATUS[int(self.action is not None and (self.action.startswith('pick_') or self.action == 'place'))]

    @property
    def video_name(self):
        """The name of the video file to use"""
        # If this is the start, then we have a special case of a noop video.
        # Handle it before anything else
        if self.start_state is None and self.action is None:
            return "{self.end_state.base_location}.{self.end_state.object_location}.{self.end_state.jug_state}.{self.end_state.bowl_state}.{self.end_state.mug_state}.noop.mp4".format(**locals())

        # First simply get the noop vs. video action
        if self.action.startswith('at_'):
            video_action = 'noop'
        else:
            video_action = self.action

        # Then update look_at_ and go_to_ action definitions based on the
        # localization params
        if video_action.startswith('look_at_') or video_action.startswith('go_to_'):
            if video_action.startswith('look_at_'):
                action_type = 'look_at_'
                location_name = video_action[len('look_at_'):]
            else:
                action_type = 'go_to_'
                location_name = video_action[len('go_to_'):]

            location_name = constants.LOCATION_NAMES[location_name]
            dt_mapping = constants.LOCATION_MAPPINGS['dining_table_to_' + constants.LOCATION_NAMES[self.start_state.current_dt_label]]
            desired_location = { v: k for k, v in dt_mapping.items() }[location_name]
            desired_location = constants.LOCATION_NAMES[desired_location]
            video_action = action_type + desired_location

        # Then, reuse the look_at_ actions if they are the reusable type
        if self.start_state.base_location == 'kc' and video_action == 'look_at_c':
            video_action = 'look_at_dt'
        elif self.start_state.base_location == 'c' and video_action == 'look_at_dt':
            video_action = 'look_at_kc'

        # Then reuse the singular videos that don't look at the objects
        object_location = self.start_state.object_location
        jug_state, bowl_state, mug_state = self.start_state.jug_state, self.start_state.bowl_state, self.start_state.mug_state

        if self.start_state.base_location == 'c' and video_action == 'noop':
            object_location = 'kc'
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'dt' and self.start_state.object_location == 'kc' and video_action == 'noop' and self.start_state.mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'kc' and self.start_state.object_location == 'dt' and video_action == 'noop' and self.start_state.mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'dt' and self.start_state.object_location == 'kc' and video_action == 'look_at_c' and self.start_state.mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'dt' and self.start_state.object_location == 'kc' and video_action == 'go_to_c' and self.start_state.mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'c' and self.start_state.object_location == 'kc' and video_action == 'go_to_dt':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        elif self.start_state.base_location == 'kc' and self.start_state.object_location == 'dt' and video_action == 'go_to_c' and self.start_state.mug_state != 'gripper':
            jug_state, bowl_state, mug_state = 'default', 'above_mug', 'default'

        return "{self.start_state.base_location}.{object_location}.{jug_state}.{bowl_state}.{mug_state}.{video_action}.mp4".format(**locals())

    # Methods
    @staticmethod
    def get_end_state(state, action):
        """
        Given a state and an action, get the end state that should result from
        them. If the action is not applicable in this state, return None
        """
        # First we check to see if the action is applicable in the state
        end_state = None

        # Cache some of the attributes
        relocalized_base_location = state.relocalized_base_location
        graspable_objects = state.graspable_objects

        # Get some attributes about the action
        if action.startswith('at_'):
            location_name = action[len('at_'):]
        elif action.startswith('go_to_'):
            location_name = action[len('go_to_'):]
        elif action.startswith('look_at_'):
            location_name = action[len('look_at_'):]
        else:
            location_name = None

        if action.startswith('pick_'):
            object_name = action[len('pick_'):]
        else:
            object_name = None

        # Do not allow AT(X), GOTO(X), LOOK_AT(X) if we are at X (according
        # to the localization)
        if location_name is not None and constants.LOCATION_NAMES[location_name] == relocalized_base_location:
            return end_state

        # Do not allow a place if the gripper is empty or if the mug is in there
        if (state.gripper_empty or state.gripper_state == 'mug') and action == 'place':
            return end_state

        # Do not allow a pick of an object if it is not graspable
        if object_name is not None and object_name not in graspable_objects:
            return end_state

        # Do not allow anything that is not localization if we are at the couch
        # with the mug but we are mislocalized
        if state.base_location == 'c' and state.current_dt_label != 'dt' and state.mug_state == 'gripper' and not action.startswith('at_'):
            return end_state

        # Then we use custom rules to update the state according to the action
        end_state = State(state)
        if action.startswith('at_'):
            base_location = constants.LOCATION_NAMES[state.base_location]
            location_name = constants.LOCATION_NAMES[location_name]

            # Find the appropriate mapping and set the end state to that
            for mapping_name, mapping in constants.LOCATION_MAPPINGS.items():
                if mapping[base_location] == location_name:
                    end_state.current_dt_label = constants.LOCATION_NAMES[mapping['dining_table']]
                    break

        elif action.startswith('go_to_'):
            dt_mapping = constants.LOCATION_MAPPINGS['dining_table_to_' + constants.LOCATION_NAMES[state.current_dt_label]]
            location_name = constants.LOCATION_NAMES[location_name]
            desired_location = { v: k for k,v in dt_mapping.items() }[location_name]
            desired_location = constants.LOCATION_NAMES[desired_location]
            end_state.base_location = desired_location

        elif action.startswith('look_at_'):
            # This is a no-op in terms of the state change
            pass

        elif action.startswith('pick_'):
            end_state.gripper_state = object_name
            setattr(end_state, object_name + '_state', 'gripper')

        elif action == 'place':
            end_state.gripper_state = constants.EMPTY_GRIPPER

        else:
            raise NotImplementedError("Unknown action: {}".format(action))

        # Return the result
        return end_state


# TODO: Create helper methods for suggesting diagnoses and actions to take
