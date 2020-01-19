import React from 'react';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { DIAGNOSIS_ORDER } from '../actions';


/** The action controls view */
class DiagnosisControls extends React.Component {
    constructor(props) {
        super(props);

        // The state definition
        this.state = {
            selected_diagnoses: []
        };
    }

    render() {
        let controls_display = DIAGNOSIS_ORDER.map((diagnosis) => {
            return (
                <button className={"btn btn-outline-secondary" + (this.state.selected_diagnoses.includes(diagnosis) ? " active" : "")}
                        style={{ width: (100/DIAGNOSIS_ORDER.length) + "%"}}
                        key={diagnosis}>
                    {window.constants.DIAGNOSES[diagnosis]}
                </button>
            );
        });

        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>The errors in the system that you are trying to resolve. Select only if you're sure</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Confirmed Errors</b>
                </p>
                </div>
                <div className="row">
                <div className="col btn-group btn-group-toggle">
                    {controls_display}
                </div>
                </div>
                <div className="row mt-2">
                <div className="offset-8 col">
                    <button className="btn btn-block btn-primary" disabled={true}>Confirm</button>
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default DiagnosisControls;
