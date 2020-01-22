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
            <button className="btn btn-outline-info btn-block"
                    style={{height: "100%", minHeight: "4rem"}}
                    onClick={this.select_action}>
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
        dx_confirmed: state.ui_status.confirmed_dx.length > 0
    };
}

/** The action controls view */
class ActionControls extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.NUMBER_BUTTONS_PER_ROW = 2;
    }

    render() {
        // Short circuit if the UI element should not be displayed
        if (!this.props.video_loaded || !!this.props.video_playing || !this.props.dx_confirmed) {
            return "";
        }

        // Calculate how to display the buttons
        let action_buttons = [];
        let sublist = [];
        for (const [idx, action] of this.props.valid_actions.entries()) {
        // for (const [idx, action] of ACTIONS_ORDER.entries()) {
            sublist.push(
                <div className="col" key={action}><ActionControlButton dispatch={this.props.dispatch} value={action} /></div>
            );

            // We want to close off after every sublist has x elements
            if (sublist.length === this.NUMBER_BUTTONS_PER_ROW) {
                action_buttons.push(<div className="row my-1" key={Math.floor(idx / this.NUMBER_BUTTONS_PER_ROW)}>{sublist}</div>);
                sublist = [];
            }
        }

        // Pad the list if we have more buttons to display
        if (sublist.length !== 0) {
            for (let idx = (sublist.length % this.NUMBER_BUTTONS_PER_ROW); idx < this.NUMBER_BUTTONS_PER_ROW; idx++) {
                sublist.push(<div className="col" key={idx}></div>);
            }
            action_buttons.push(<div className="row my-1" key={-1}>{sublist}</div>);
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
