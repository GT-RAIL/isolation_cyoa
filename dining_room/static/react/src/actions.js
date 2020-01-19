/**
 * Actions defined for the app. These include utilities to fetch data from the
 * server, etc.
 */


// The action types (in almost expected chronological order)
export const UPDATE_STATE = 'UPDATE_STATE';

export const PLAY_VIDEO = 'PLAY_VIDEO';
export const DISPLAY_STATE = 'DISPLAY_STATE';

export const UPDATE_HISTORY = 'UPDATE_HISTORY';
export const COMPLETE_SCENARIO = 'COMPLETE_SCENARIO';

export const SELECT_DIAGNOSIS = 'SELECT_DIAGNOSIS';
export const SELECT_ACTION = 'SELECT_ACTION';


// Other constants

// TBD


// Action Creators

export function updateState(new_state) {
    return { type: UPDATE_STATE, new_state};
}

export function playVideo() {
    return { type: PLAY_VIDEO };
}

export function displayState() {
    return { type: DISPLAY_STATE };
}

export function updateHistory(history_item) {
    return { type: UPDATE_HISTORY, history_item };
}

export function completeScenario() {
    return { type: COMPLETE_SCENARIO };
}

export function selectDiagnosis(diagnosis) {
    return { type: SELECT_DIAGNOSIS, diagnosis };
}

export function selectAction(action) {
    return { type: SELECT_ACTION, action };
}
