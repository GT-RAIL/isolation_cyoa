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

export const CONFIRM_DIAGNOSES = 'CONFIRM_DIAGNOSES';
export const SELECT_ACTION = 'SELECT_ACTION';


// Other constants

// The order in which to present diagnoses and actions
export const DIAGNOSIS_ORDER = [
    'lost',
    'cannot_pick',
    'cannot_see',
    'different_location',
    'unknown',
    'none'
];

export const ACTIONS_ORDER = [
    'at_c',
    'at_dt',
    'at_kc',
    'go_to_c',
    'go_to_dt',
    'go_to_kc',
    'look_at_c',
    'look_at_dt',
    'look_at_kc',
    'pick_bowl',
    'pick_jug',
    'pick_mug',
    'place'
];


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

export function confirmDiagnoses(diagnoses) {
    return { type: CONFIRM_DIAGNOSES, diagnoses };
}

export function selectAction(action) {
    return { type: SELECT_ACTION, action };
}
