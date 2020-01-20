import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import { DIAGNOSIS_ORDER } from '../actions';
import { confirmDiagnoses } from '../actions';


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
        // is updated, which is what we want
        this.state = {
            selected_diagnoses: [...this.props.confirmed_dx]
        };

        // Bind the functions
        this.select_diagnosis = this.select_diagnosis.bind(this);
        this.confirm_diagnoses = this.confirm_diagnoses.bind(this);
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

    confirm_diagnoses(e) {
        this.props.dispatch(confirmDiagnoses(this.state.selected_diagnoses));
    }

    render() {
        // Short circuit if the UI element should not be displayed
        if (!this.props.video_loaded || !!this.props.video_playing) {
            return "";
        }

        let controls_display = DIAGNOSIS_ORDER.map((diagnosis) => {
            return (
                <button className={"btn btn-outline-primary" + (this.state.selected_diagnoses.includes(diagnosis) ? " active" : "")}
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
                    <OverlayTrigger placement="right" overlay={<Tooltip>The errors in the system that you are trying to resolve. Select only if you're sure</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Confirmed Errors</b>
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
                            onClick={this.confirm_diagnoses}>
                        Confirm
                    </button>
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default connect(mapStateToProps)(DiagnosisControls);
