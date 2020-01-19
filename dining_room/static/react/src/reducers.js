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
    UPDATE_HISTORY,
    COMPLETE_SCENARIO,
    SELECT_DIAGNOSIS,
    SELECT_ACTION
} from './actions';


// Each of the reducers

/** Handle updates to the status of the UI based on the incoming action */
function ui_status(
    state={
        video_loaded: false,
        video_playing: false,
        state_to_process: null,
        selected_dx: null,
        selected_ax: null
    },
    action
) {
    switch (action.type) {

        // The default
        default:
            return state;
    }
}


/** Handle updates to the state of the scenario based on the incoming action */
function scenario_state(state={}, action) {
    switch (action.type) {

        // The default
        default:
            return state;
    }
}


/** Handle updates to the history */
function history(state=[], action) {
    switch (action.type) {

        // The default
        default:
            return state;
    }
}


/** Handle updates to the transition data */
function transition(state={}, action) {
    switch (action.type) {

        // The default
        default:
            return state;
    }
}


/** Finally the app (and the corresponding state definition) */

const AppState = combineReducers({ ui_status, scenario_state, history, transition });

export default AppState;
