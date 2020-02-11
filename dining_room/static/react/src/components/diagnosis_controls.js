import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { selectDiagnoses } from '../actions';


/** The button for diagnoses */
const DiagnosisControlButton = (props) => {
    // This breaks the nice flow of information, but for now, we'll allow it
    let suggest = (!!window.constants.EXPERIMENT_CONDITION.show_dx_suggestions && !!props.suggested) && !props.disabled;
    let button_colour = (!!suggest || !window.constants.EXPERIMENT_CONDITION.show_dx_suggestions)
                        ? " btn-outline-info"
                        : " btn-outline-secondary";
    // let button_colour = " btn-outline-info";

    return (
        <button className={"mx-1 col btn" + button_colour + (!!props.selected ? " active font-weight-bold" : "")}
                type="button"
                style={{
                    minHeight: "4rem",
                    borderWidth: (!!suggest) ? "3px" : "",
                    pointerEvents: (!!props.disabled ? "none" : "auto")
                }}
                value={props.value}
                onClick={props.select_diagnosis}>
            {window.constants.DIAGNOSES[props.value]}
        </button>
    );
}


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        confirmed_dx: state.ui_status.confirmed_dx,
        suggestions: state.scenario_state.dx_suggestions,
    };
}

/** The diagnosis controls view */
class DiagnosisControls extends React.Component {
    constructor(props) {
        super(props);

        // The state definition (this should only change when the video status)
        // is updated, which is what we want. This does not follow the
        // recommendations in the React docs, because I don't know how to
        // follow them for this component without creating an unnecessary
        // wrapper component.
        this.state = { selected_diagnoses: [] };

        // Constants
        this.BUTTONS_LAYOUT = [
            {
                name: 'Location faults',
                diagnoses: window.constants.DIAGNOSES_ORDER.slice(0, 4),
            },
            {
                name: 'Object faults',
                diagnoses: window.constants.DIAGNOSES_ORDER.slice(4, 8),
            },
            {
                name: 'Miscellaneous & None',
                diagnoses: window.constants.DIAGNOSES_ORDER.slice(8, 11),
            },
        ];

        // Inferred property
        this.MAX_BUTTONS_PER_ROW = 0;
        for (const [idx, display_object] of this.BUTTONS_LAYOUT.entries()) {
            if (display_object.diagnoses.length > this.MAX_BUTTONS_PER_ROW) {
                this.MAX_BUTTONS_PER_ROW = display_object.diagnoses.length;
            }
        }

        // Bind the functions
        this.select_diagnosis = this.select_diagnosis.bind(this);
        this.select_diagnoses = this.select_diagnoses.bind(this);
    }

    static getDerivedStateFromProps(props, state) {
        // If the video is not playing and has been loaded, then use your own
        // state. If not, shadow the incoming props
        if (!!props.video_loaded && !props.video_playing) {
            return state;
        } else {
            return { selected_diagnoses: props.confirmed_dx };
        }
    }

    select_diagnosis(e) {
        let diagnosis = e.target.value;
        let new_selection = [...this.state.selected_diagnoses];
        if (new_selection.includes(diagnosis)) {
            new_selection.splice(new_selection.indexOf(diagnosis), 1);
        } else {
            new_selection.push(diagnosis);
        }
        this.setState({ selected_diagnoses: new_selection });
    }

    select_diagnoses(e) {
        this.props.dispatch(selectDiagnoses(this.state.selected_diagnoses));
    }

    render() {
        // Short circuit if the UI element should not be displayed
        if (!this.props.video_loaded || !!this.props.video_playing) {
            return "";
        }

        // Calculate how to display the controls
        let diagnoses_buttons = [];
        for (const [didx, display_object] of this.BUTTONS_LAYOUT.entries()) {

            // Create buttons according to the data
            let sublayout = [];
            for (const [sidx, diagnosis] of display_object.diagnoses.entries()) {
                sublayout.push(
                    <DiagnosisControlButton key={diagnosis}
                                            value={diagnosis}
                                            disabled={this.props.confirmed_dx.length > 0}
                                            selected={this.state.selected_diagnoses.includes(diagnosis)}
                                            select_diagnosis={this.select_diagnosis}
                                            suggested={this.props.suggestions.includes(diagnosis)} />
                );
            }

            // Pad the sublayout
            for (let idx = sublayout.length; idx < this.MAX_BUTTONS_PER_ROW; idx++) {
                sublayout.push(<div className="mx-1 btn col invisible" key={idx}></div>);
            }

            // Add the row of buttons
            diagnoses_buttons.push(
                <div className="row my-1" key={display_object.name}>
                    {sublayout}
                </div>
            );
        }

        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>Select the problem(s) in the current situation you observe or are trying to resolve</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>What do you think is interfering with the robot's ability to achieve its goal?</b>
                </p>
                </div>
                    {diagnoses_buttons}
                <div className="row mt-2">
                <div className="offset-8 col">
                    <button className="btn btn-block btn-success"
                            disabled={this.state.selected_diagnoses.length === 0 || this.props.confirmed_dx.length > 0}
                            onClick={this.select_diagnoses}>
                        Select
                    </button>
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default connect(mapStateToProps)(DiagnosisControls);
