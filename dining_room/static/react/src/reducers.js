/**
 * The reducers for the app. This might be a giant file based on the logic of
 * how the state changes, but it's better to keep it all in this one location
 * for now
 */

import { combineReducers } from 'redux';
import {
    UPDATE_STATE,
    PLAY_VIDEO,
    DISPLAY_STATE,
    COMPLETE_SCENARIO,
    CONFIRM_DIAGNOSES,
    SELECT_ACTION
} from './actions';


// Each of the reducers

/** Handle updates to the status of the UI based on the incoming action */
function ui_status(
    state={
        video_loaded: false,
        video_playing: false,
        confirmed_dx: [],
        scenario_completed: false,
        // Timestamps
        video_loaded_time: null,
        video_stop_time: null,
        dx_selected_time: null,
        ax_selected_time: null,
    },
    action
) {
    switch (action.type) {
        // When the video starts playing, mark it as loaded
        case PLAY_VIDEO:
            return {
                ...state,
                video_loaded: true,
                video_playing: true,
                video_loaded_time: Date.now() / 1000
            };

        // When it is time to display the state, mark the video as complete
        case DISPLAY_STATE:
            return {
                ...state,
                video_playing: false,
                video_stop_time: Date.now() / 1000
            };

        // When the scenario is completed, update the UI state
        case COMPLETE_SCENARIO:
            return {
                ...state,
                scenario_completed: true
            };

        // When diagnoses are selected, mark them as selected and update he
        // state of the UI
        case CONFIRM_DIAGNOSES:
            return {
                ...state,
                confirmed_dx: action.diagnoses
            };

        // When an action is selected, reset the video variables & send an
        //  update to the server (since this is where the user selection lives)
        case SELECT_ACTION:
            // TODO: start the process of getting data from the server
            return {
                ...state,
                video_loaded: false,
                video_playing: false,
                confirmed_dx: [],
                ax_selected_time: Date.now() / 1000
            };

        // The default
        default:
            return state;
    }
}


/** Handle updates to the state of the scenario based on the incoming action */
function scenario_state(
    state={
        video_link: "https://dl.dropboxusercontent.com/s/qxro9nj1zbf6mmf/dt.kc.gripper.default.gripper.noop.mp4",
        robot_beliefs: [
            { attr: "Location", value: "Dining Table" },
            { attr: "Object in gripper", value: "Empty" },
            { attr: "Objects in view", value: ["Jug, Bowl"] },
            { attr: "Arm status", value: "In motion" }
        ],
        valid_actions: ['at_c', 'at_dt', 'go_to_c', 'go_to_dt', 'look_at_c', 'look_at_dt', 'pick_bowl', 'pick_mug', 'place'],
        dx_suggestions: ["cannot_see"],
        ax_suggestions: ["look_at_dt", "go_to_c", "place"],
        action_result: true
    },
    action
) {
    switch (action.type) {

        // The default
        default:
            return state;
    }
}


/** Handle updates to the history */
function history(
    state={
        dx_to_add: null,
        ax_to_add: null,
        result_to_add: null,
        history: [
            { error: ["Something was wrong"], action: "An action", result: true },
            { error: ["Something else was wrong", "Something was wrong"], action: "Another action", result: true },
            { error: ["Unknown"], action: "Yet another action", result: false },
            { error: ["Something was wrong"], action: "An action", result: true },
            { error: ["It was wrong", "Something was wrong"], action: "Another action", result: true },
            { error: ["Unknown", "Something very wrong"], action: "Yet another action", result: false }
        ]
    },
    action
) {
    switch (action.type) {
        // When the video is done playing, update the history if there are
        // items in the buffer to update
        case DISPLAY_STATE:
            if (!state.dx_to_add || !state.ax_to_add) {
                return state;
            }

            return {
                dx_to_add: null,
                ax_to_add: null,
                result_to_add: null,
                history: [...state.history, { error: state.dx_to_add, action: state.ax_to_add, result: state.result_to_add }]
            };

        // When the state is updated, get the result from the state
        case UPDATE_STATE:
            return {
                ...state,
                result_to_add: action.new_state.action_result
            };

        // When a diagnosis is confirmed, add it to the to be updated history
        // event
        case CONFIRM_DIAGNOSES:
            return {
                ...state,
                dx_to_add: action.diagnoses
            };

        // When an action is selected, add it to the action to update
        case SELECT_ACTION:
            return {
                ...state,
                ax_to_add: action.action
            };

        // The default
        default:
            return state;
    }
}


/** Finally the app (and the corresponding state definition) */

const AppState = combineReducers({ ui_status, scenario_state, history });

export default AppState;
