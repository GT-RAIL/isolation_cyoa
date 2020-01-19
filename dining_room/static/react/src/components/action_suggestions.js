import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


/** The action suggestions view */
class ActionSuggestions extends React.Component {
    constructor(props) {
        super(props);

        // The state definition (these should be props)
        this.state = {
            suggested_actions: ["An action", "Another action", "Yet another action"]
        }
    }

    render() {
        let suggestions_display = this.state.suggested_actions.map((action) => {
            return <li key={action}>{action}</li>;
        });

        return (
            <div className="row">
            <p className="col">
                <OverlayTrigger placement="right" overlay={<Tooltip>Actions the robot thinks might help gather more information or resolve the error</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Recommended Actions</b>
            </p>
            <div className="col-9">
            <ul className="list-unstyled">
                {suggestions_display}
            </ul>
            </div>
            </div>
        );
    }
}

export default ActionSuggestions;
