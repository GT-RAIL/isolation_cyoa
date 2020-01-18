import React from 'react';

import DiagnosisSuggestions from './diagnosis_suggestions';
import ActionSuggestions from './action_suggestions';


class Suggestions extends React.Component {
    /** The suggestions view */
    render() {
        let diagnosis_suggestions =
            (!!this.props.show_dx_suggestions && this.props.video_status.video_loaded && !this.props.video_status.video_playing)
            ? <DiagnosisSuggestions />
            : <div className="d-none" />;
        let action_suggestions =
            (!!this.props.show_ax_suggestions && this.props.video_status.video_loaded && !this.props.video_status.video_playing)
            ? <ActionSuggestions />
            : <div className = "d-none" />;

        return (
            <div className="row">
            <div className="col">
                {diagnosis_suggestions}
                <div className={(!!this.props.show_dx_suggestions && !!this.props.show_ax_suggestions) ? "my-3" : "d-none"} />
                {action_suggestions}
            </div>
            </div>
        );
    }
}

export default Suggestions;
