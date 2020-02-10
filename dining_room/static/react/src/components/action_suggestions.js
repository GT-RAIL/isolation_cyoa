import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        suggestions: state.scenario_state.ax_suggestions
    };
}

/** The action suggestions view */
const ActionSuggestions = (props) => {
    // Short circuit if the UI element should not be displayed
    if (!props.video_loaded || !!props.video_playing) {
        return "";
    }

    let suggestions_display = props.suggestions.map((action) => {
        return <li key={action}><h5>{window.constants.ACTIONS[action]}</h5></li>;
    });

    return (
        <div className="row">
        <p className="col">
            <OverlayTrigger placement="right" overlay={<Tooltip>Actions the robot thinks might help you gather more information about the problem, or help resolve it</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Recommended Actions</b>
        </p>
        <div className="col-9">
        <ul className="list-unstyled">
            {suggestions_display}
        </ul>
        </div>
        </div>
    );
}

export default connect(mapStateToProps)(ActionSuggestions);
