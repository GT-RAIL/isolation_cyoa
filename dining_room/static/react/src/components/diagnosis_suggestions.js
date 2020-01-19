import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { DIAGNOSIS_ORDER } from '../actions';


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        suggestions: state.scenario_state.dx_suggestions
    };
}


/** The diagnosis suggestions view */
const DiagnosisSuggestions = (props) => {
    let suggestions_display = DIAGNOSIS_ORDER.map((diagnosis) => {
        return (
            <button className={"btn btn-outline-dark" + (props.suggestions.includes(diagnosis) ? " active" : "")}
                    style={{ width: (100/DIAGNOSIS_ORDER.length) + "%", pointerEvents: "none" }}
                    key={diagnosis}>
                {window.constants.DIAGNOSES[diagnosis]}
            </button>
        );
    });

    return (
        <div className={"row" + ((!!props.video_loaded && !props.video_playing) ? "" : " d-none") }>
        <div className="col">
            <div className="row">
            <p className="col">
                <OverlayTrigger placement="right" overlay={<Tooltip>The errors that the robot thinks might be present right now</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Possible Errors</b>
            </p>
            </div>
            <div className="row">
            <div className="col btn-group btn-group-toggle">
                {suggestions_display}
            </div>
            </div>
        </div>
        </div>
    );
}

export default connect(mapStateToProps)(DiagnosisSuggestions);
