import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


class DiagnosisSuggestions extends React.Component {
    /** The diagnosis suggestions view */
    render() {
        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>The errors that the robot thinks might be present right now</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Possible Errors</b>
                </p>
                </div>
                <div className="row">
                <div className="col btn-group btn-group-toggle">
                    <button className="btn btn-outline-dark" style={{ width: "20%", pointerEvents: "none" }}>The robot is lost</button>
                    <button className="btn btn-outline-dark active" style={{ width: "20%", pointerEvents: "none" }}>The mug cannot be picked up</button>
                    <button className="btn btn-outline-dark" style={{ width: "20%", pointerEvents: "none" }}>The mug is not visible</button>
                    <button className="btn btn-outline-dark" style={{ width: "20%", pointerEvents: "none" }}>The mug is not where is should be</button>
                    <button className="btn btn-outline-dark" style={{ width: "20%", pointerEvents: "none" }}>Unknown /<br/>There is no error</button>
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default DiagnosisSuggestions;
