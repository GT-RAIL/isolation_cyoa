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
    SELECT_DIAGNOSES,
    CONFIRM_DIAGNOSES,
    SELECT_ACTION
} from './actions';


// Each of the reducers

/** Handle updates to the status of the UI based on the incoming action */
function ui_status(state=window.constants.INITIAL_STATE.ui_state, action) {
    switch (action.type) {
        // Reset the state of the UI when the state has been updated from server
        case UPDATE_STATE:
            return {
                ...window.constants.INITIAL_STATE.ui_state,
                selected_action_idx: state.selected_action_idx
            };

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

        // When diagnoses are selected, mark them as selected and update he
        // state of the UI
        case SELECT_DIAGNOSES:
            return {
                ...state,
                confirmed_dx: action.diagnoses,
                dx_selected_time: Date.now() / 1000
            };

        // When diagnoses are confirmed, mark the value
        case CONFIRM_DIAGNOSES:
            return {
                ...state,
                dx_certainty: action.certainty,
                dx_confirmed_time: Date.now() / 1000
            }

        // When an action is selected, update the timestamp and set the action
        case SELECT_ACTION:
            return {
                ...state,
                selected_action: action.action,
                ax_selected_time: Date.now() / 1000,
                selected_action_idx: state.selected_action_idx + 1
            };

        // The default
        default:
            return state;
    }
}


/** Handle updates to the state of the scenario based on the incoming action */
function scenario_state(state=window.constants.INITIAL_STATE.scenario_state, action) {
    switch (action.type) {
        // Simply update the state from the server as is if there was no error
        case UPDATE_STATE:
            if (!!action.new_state.server_state_tuple) {
                return action.new_state;
            } else {
                return {
                    ...state,
                    ...action.new_state
                }
            }

        // The default
        default:
            return state;
    }
}


/** Handle updates to the history */
function history(state=window.constants.INITIAL_STATE.history, action) {
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
        case SELECT_DIAGNOSES:
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
