import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


/** The action controls view */
class DiagnosisControls extends React.Component {
    constructor(props) {
        super(props);

        // The state definition (These should be props?)
        this.state = {};
    }

    render() {
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
                    <button className="btn btn-outline-secondary active" style={{ width: "20%" }}>The robot is lost</button>
                    <button className="btn btn-outline-secondary active" style={{ width: "20%" }}>The mug cannot be picked up</button>
                    <button className="btn btn-outline-secondary" style={{ width: "20%" }}>The mug is not visible</button>
                    <button className="btn btn-outline-secondary" style={{ width: "20%" }}>The mug is not where is should be</button>
                    <button className="btn btn-outline-secondary" style={{ width: "20%" }}>Unknown /<br/>There is no error</button>
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
