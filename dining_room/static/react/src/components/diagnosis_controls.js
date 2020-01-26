import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { DIAGNOSIS_ORDER } from '../actions';
import { selectDiagnoses } from '../actions';


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        confirmed_dx: state.ui_status.confirmed_dx
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

        let controls_display = DIAGNOSIS_ORDER.map((diagnosis) => {
            return (
                <button className={"btn btn-outline-info" + (this.state.selected_diagnoses.includes(diagnosis) ? " active" : "")}
                        type="button"
                        style={{
                            width: (100/DIAGNOSIS_ORDER.length) + "%",
                            pointerEvents: (this.props.confirmed_dx.length > 0 ? "none" : "auto")
                        }}
                        key={diagnosis}
                        value={diagnosis}
                        onClick={this.select_diagnosis}>
                    {window.constants.DIAGNOSES[diagnosis]}
                </button>
            );
        });

        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>Select the problems in the current situation you observe or are trying to resolve</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>What do you think is interfering with the robot's ability to achieve its goal?</b>
                </p>
                </div>
                <div className="row">
                <div className="col btn-group btn-group-toggle">
                    {controls_display}
                </div>
                </div>
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
