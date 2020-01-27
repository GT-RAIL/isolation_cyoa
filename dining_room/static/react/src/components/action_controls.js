import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { ACTIONS_ORDER } from '../actions';
import { fetchNextState } from '../actions';


/** The button for an action */
class ActionControlButton extends React.Component {
    constructor(props) {
        super(props);

        // Bind the functions
        this.select_action = this.select_action.bind(this);
    }

    select_action(e) {
        this.props.dispatch(fetchNextState(this.props.value));
    }

    render() {
        return (
            <button className={"btn btn-block " + (!!this.props.disabled ? "btn-outline-secondary" : "btn-outline-info")}
                    style={{height: "100%", minHeight: "4rem"}}
                    onClick={this.select_action}
                    disabled={this.props.disabled}>
                {window.constants.ACTIONS[this.props.value]}
            </button>
        );
    }
}


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        valid_actions: state.scenario_state.valid_actions,
        dx_confirmed: state.ui_status.confirmed_dx.length > 0,
        dx_certainty: state.ui_status.dx_certainty
    };
}

/** The action controls view */
class ActionControls extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.BUTTONS_LAYOUT = [
            {
                name: "Update location beliefs",
                actions: ['at_c', 'at_dt', 'at_kc']
            },
            {
                name: "Navigate",
                actions: ['go_to_c', 'go_to_kc', 'go_to_dt']
            },
            {
                name: "Look at",
                actions: ['look_at_c', 'look_at_kc', 'look_at_dt']
            },
            {
                name: "Pick",
                actions: ['pick_jug', 'pick_bowl', 'pick_mug']
            },
            {
                name: "Put away",
                actions: ['place']
            }
        ];

        // Inferred property
        this.MAX_BUTTONS_PER_ROW = 0;
        for (const [idx, display_object] of this.BUTTONS_LAYOUT.entries()) {
            if (display_object.actions.length > this.MAX_BUTTONS_PER_ROW) {
                this.MAX_BUTTONS_PER_ROW = display_object.actions.length;
            }
        }
    }

    render() {
        // Short circuit if the UI element should not be displayed
        if (!this.props.video_loaded || !!this.props.video_playing || !this.props.dx_confirmed || !this.props.dx_certainty) {
            return "";
        }

        // Calculate how to display the buttons
        let action_buttons = [];
        for (const [didx, display_object] of this.BUTTONS_LAYOUT.entries()) {

            // Create the buttons and set disabled according to the data
            let sublayout = [];
            for (const [sidx, action_name] of display_object.actions.entries()) {
                sublayout.push(
                    <div className="col" key={action_name}>
                    <ActionControlButton dispatch={this.props.dispatch} value={action_name} disabled={!this.props.valid_actions[action_name]} />
                    </div>
                );
            }
            for (let idx = sublayout.length; idx < this.MAX_BUTTONS_PER_ROW; idx++) {
                sublayout.push(<div className="col" key={idx}></div>);
            }

            // Add the buttons in a row
            action_buttons.push(
                <div className="row my-1" key={display_object.name}>{sublayout}</div>
            );
        }

        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>Select the next action that the robot should take to eventually achieve its goal</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>What action should the robot take to move towards its goal?</b>
                </p>
                </div>
                {action_buttons}
            </div>
            </div>
        );
    }
}

export default connect(mapStateToProps)(ActionControls);
export { ActionControlButton };
