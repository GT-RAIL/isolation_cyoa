/**
 * Actions defined for the app. These include utilities to fetch data from the
 * server, etc.
 */


// The action types (in almost expected chronological order)
export const UPDATE_STATE = 'UPDATE_STATE';

export const PLAY_VIDEO = 'PLAY_VIDEO';
export const DISPLAY_STATE = 'DISPLAY_STATE';

export const SELECT_DIAGNOSES = 'SELECT_DIAGNOSES';
export const CONFIRM_DIAGNOSES = 'CONFIRM_DIAGNOSES';
export const SELECT_ACTION = 'SELECT_ACTION';


// Other constants

// The order in which to present diagnoses and actions
export const DIAGNOSIS_ORDER = [
    'lost',
    'cannot_pick',
    'cannot_see',
    'different_location',
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

export function fetchNextState(action) {
    // Asynchronous call to get the state
    return (dispatch, getState) => {
        // Update the information about the action
        dispatch(selectAction(action));

        // Get the state and send the data to the server. Parse the response
        // and then send an updated state action
        let state = getState();
        return fetch(
                window.constants.NEXT_STATE_URL,
                {
                    method: 'POST',
                    mode: 'cors',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        server_state_tuple: state.scenario_state.server_state_tuple,
                        action: action,
                        ui_state: state.ui_status
                    })
                }
            )
            .then((response) => response.json())
            .then((state) => dispatch(updateState(state)))
            .catch(console.error);
    }
}

export function updateState(new_state) {
    return { type: UPDATE_STATE, new_state};
}

export function playVideo() {
    return { type: PLAY_VIDEO };
}

export function displayState() {
    return { type: DISPLAY_STATE };
}

export function selectDiagnoses(diagnoses) {
    return { type: SELECT_DIAGNOSES, diagnoses };
}

export function confirmDiagnoses(certainty) {
    return { type: CONFIRM_DIAGNOSES, certainty };
}

export function selectAction(action) {
    // Don't call this when an action is selected, call the `fetchNextState`
    // action instead (this is because of how redux seems to work)
    return { type: SELECT_ACTION, action };
}
