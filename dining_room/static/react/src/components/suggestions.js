import React from 'react';

import DiagnosisSuggestions from './diagnosis_suggestions';
import ActionSuggestions from './action_suggestions';


class Suggestions extends React.Component {
    /** The suggestions view */
    render() {
        return (
            <div className="row">
            <div className="col">
                <DiagnosisSuggestions />
                <ActionSuggestions />
            </div>
            </div>
        );
    }
}

export default Suggestions;
