import React from 'react';

import ActionControls from './action_controls';
import DiagnosisControls from './diagnosis_controls';


class Controls extends React.Component {
    /** The controls view */
    render() {
        return (
            <div className="row">
            <div className="col">
                <DiagnosisControls />
                <ActionControls />
            </div>
            </div>
        );
    }
}

export default Controls;
