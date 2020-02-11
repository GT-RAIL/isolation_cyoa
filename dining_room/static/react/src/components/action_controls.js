import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

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
        let suggest = (!!window.constants.EXPERIMENT_CONDITION.show_ax_suggestions && !!this.props.suggested) && !this.props.disabled;
        let button_colour = (!!suggest || !window.constants.EXPERIMENT_CONDITION.show_ax_suggestions)
                            ? " btn-outline-info"
                            : " btn-outline-secondary";
        // let button_colour = " btn-outline-info";

        button_colour = (!!this.props.disabled ? " btn-outline-secondary" : button_colour);

        return (
            <button className={"col btn" + button_colour}
                    style={{
                        height: "100%",
                        minHeight: "4rem",
                        borderWidth: (!!suggest) ? "3px" : "",
                    }}
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
        dx_certainty: state.ui_status.dx_certainty,
        selected_action: state.ui_status.selected_action,
        suggestions: state.scenario_state.ax_suggestions,
    };
}

/** The action controls view */
class ActionControls extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.BUTTONS_LAYOUT = [
            {
                name: "Update location belief",
                actions: window.constants.ACTIONS_ORDER.slice(0, 3),
            },
            {
                name: "Navigate",
                actions: window.constants.ACTIONS_ORDER.slice(3, 6),
            },
            {
                name: "",
                actions: window.constants.ACTIONS_ORDER.slice(6, 8),
            },
            {
                name: "Look at",
                actions: window.constants.ACTIONS_ORDER.slice(8, 11),
            },
            {
                name: "Pick",
                actions: window.constants.ACTIONS_ORDER.slice(11, 14),
            },
            {
                name: "Place",
                actions: window.constants.ACTIONS_ORDER.slice(14, 15),
            },
            {
                name: "Hardware & Drivers",
                actions: window.constants.ACTIONS_ORDER.slice(15, 17)
            }

            // {
            //     name: "Update location beliefs",
            //     actions: window.constants.ACTIONS_ORDER.slice(0, 3),
            // },
            // {
            //     name: "Navigate",
            //     actions: window.constants.ACTIONS_ORDER.slice(3, 6),
            // },
            // {
            //     name: "Nav Distractor",
            //     actions: window.constants.ACTIONS_ORDER.slice(6, 9),
            // },
            // {
            //     name: "Look at",
            //     actions: window.constants.ACTIONS_ORDER.slice(9, 12),
            // },
            // {
            //     name: "Pick",
            //     actions: window.constants.ACTIONS_ORDER.slice(12, 15),
            // },
            // {
            //     name: "Place",
            //     actions: window.constants.ACTIONS_ORDER.slice(15, 17),
            // },
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

            // Create the buttons according to the data
            let sublayout = [];
            for (const [sidx, action_name] of display_object.actions.entries()) {
                sublayout.push(
                    <ActionControlButton key={action_name}
                                         dispatch={this.props.dispatch}
                                         value={action_name}
                                         disabled={!!this.props.selected_action}
                                         suggested={this.props.suggestions.includes(action_name)} />
                );
            }
            for (let idx = sublayout.length; idx < this.MAX_BUTTONS_PER_ROW; idx++) {
                sublayout.push(<div className="btn col invisible" key={idx}></div>);
            }

            // Add row of buttons
            action_buttons.push(
                <div className="row my-1" key={display_object.name}>
                <div className="col">
                    <div className="row">
                    <p className="col my-0"><small>{display_object.name}</small></p>
                    </div>
                    <div className="row">
                    <div className="col btn-group">
                        {sublayout}
                    </div>
                    </div>
                </div>
                </div>
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
