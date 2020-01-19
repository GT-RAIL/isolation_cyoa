import React from 'react';

import ActionControls from './action_controls';
import DiagnosisControls from './diagnosis_controls';


/** The controls view */
const Controls = (props) => {
    return (
        <div className="row">
        <div className="col">
            <DiagnosisControls />
            <div className="my-3" />
            <ActionControls />
        </div>
        </div>
    );
};

export default Controls;
