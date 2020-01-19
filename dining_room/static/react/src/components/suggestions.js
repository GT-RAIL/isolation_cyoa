import React from 'react';

import DiagnosisSuggestions from './diagnosis_suggestions';
import ActionSuggestions from './action_suggestions';


/** The suggestions view */
const Suggestions = (props) => {
    let diagnosis_suggestions = (!!props.show_dx_suggestions)
                                ? <DiagnosisSuggestions />
                                : <div className="d-none" />;
    let action_suggestions = (!!props.show_ax_suggestions)
                             ? <ActionSuggestions />
                             : <div className = "d-none" />;

    return (
        <div className="row">
        <div className="col">
            {diagnosis_suggestions}
            <div className={(!!props.show_dx_suggestions && !!props.show_ax_suggestions) ? "my-3" : "d-none"} />
            {action_suggestions}
        </div>
        </div>
    );
}

export default Suggestions;
