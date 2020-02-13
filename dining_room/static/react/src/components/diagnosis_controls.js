import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';
import { faStar } from '@fortawesome/free-solid-svg-icons/faStar';

import { selectDiagnoses } from '../actions';


/** The button for diagnoses */
class DiagnosisControlButton extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.DEFAULT_BUTTON_COLOUR = ' btn-outline-info';
        this.DISABLED_BUTTON_COLOUR = ' btn-outline-secondary';
    }

    render() {
        // Pick the button colour
        let suggest = (!!this.props.show_suggestions && !!this.props.suggested && !this.props.disabled);
        let button_colour = this.DEFAULT_BUTTON_COLOUR;

        // Add stars to the button if it's suggested
        let star_marks = [];
        if (!!suggest) {
            for (let i = 0; i < this.props.suggested_imp; i++) {
                star_marks.push(<FontAwesomeIcon icon={faStar} key={i} />);
            }
            star_marks.push(<br key={-1}/>);
        }

        return (
            <button className={"mx-1 col btn" + button_colour + (!!this.props.selected ? " active font-weight-bold" : "")}
                    type="button"
                    style={{
                        minHeight: "4rem",
                        pointerEvents: (!!this.props.disabled ? "none" : "auto"),
                        fontSize: "1.25rem",
                        fontWeight: "300",
                    }}
                    value={this.props.value}
                    onClick={this.props.select_diagnosis}>
                {star_marks}{window.constants.DIAGNOSES[this.props.value]}
            </button>
        );
    }
}


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        confirmed_dx: state.ui_status.confirmed_dx,
        suggestions: state.scenario_state.dx_suggestions,
        show_suggestions: !!window.constants.EXPERIMENT_CONDITION.show_dx_suggestions,
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
        console.log("selected "+diagnosis);
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
                let suggest = this.props.suggestions.includes(diagnosis);
                let suggestion_idx = this.props.suggestions.indexOf(diagnosis); // -1, or idx
                let suggestion_imp = (!!suggest) ? this.props.suggestions.length - suggestion_idx : 0;

                sublayout.push(
                    <DiagnosisControlButton key={diagnosis}
                                            value={diagnosis}
                                            disabled={this.props.confirmed_dx.length > 0}
                                            selected={this.state.selected_diagnoses.includes(diagnosis)}
                                            select_diagnosis={this.select_diagnosis}
                                            show_suggestions={this.props.show_suggestions}
                                            suggested={suggest}
                                            suggested_idx={suggestion_idx}
                                            suggested_imp={suggestion_imp} />
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

        // Add additional instructions if necessary
        let extra_instructions = !!this.props.show_suggestions
                                 ? (<small><br/>The robot might put a star on the problem(s) it thinks might be stopping it from reaching its goal. <b>The more stars, the more certain the robot might be</b>.</small>)
                                 : "";
        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>Select the problem(s) in the current situation you observe or are trying to resolve</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>What do you think is interfering with the robot's ability to achieve its goal?</b>{extra_instructions}
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
