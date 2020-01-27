import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

import Slider from 'bootstrap-slider';

import { confirmDiagnoses } from '../actions';


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing,
        dx_confirmed: state.ui_status.confirmed_dx.length > 0,
        dx_certainty: state.ui_status.dx_certainty
    };
}

/** The diagnosis certainty controls view */
class DiagnosisCertaintyControls extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.MAX_VALUE = 5;
        this.MIN_VALUE = 1;
        this.DEFAULT_VALUE = 3;

        // Initialize the state
        this.state = {};

        // Bind the functions
        this.confirm_diagnoses = this.confirm_diagnoses.bind(this);

        // Refs
        this.sliderRef = React.createRef();
        this.slider = null;
    }

    create_slider() {
        this.slider = new Slider("input.slider", {
            min: this.MIN_VALUE,
            max: this.MAX_VALUE,
            step: 1,
            value: this.props.dx_certainty || this.DEFAULT_VALUE,
            tooltip: "hide",
            ticks: [1, 2, 3, 4, 5]
        });
        this.slider.enable();
    }

    destroy_slider() {
        this.slider.destroy();
        this.slider = null;
    }

    componentDidMount() {
        if (!!this.sliderRef.current && !this.slider) {
            this.create_slider();
        }
    }

    componentDidUpdate() {
        if (!!this.sliderRef.current && !this.slider) {
            this.create_slider();
        } else if (!this.sliderRef.current && !!this.slider) {
            this.destroy_slider();
        }
    }

    componentWillUnmount() {
        if (!!this.slider) {
            this.destroy_slider();
        }
    }

    confirm_diagnoses(e) {
        this.props.dispatch(confirmDiagnoses(this.slider.getValue()));
        this.slider.disable();
    }

    render() {
        // Short circuit if the UI element should not be displayed
        if (!this.props.video_loaded || !!this.props.video_playing || !this.props.dx_confirmed) {
            return "";
        }

        return (
            <div className="row">
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>Indicate on the scale how certain you are of the problems that you have identified</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>How sure are you of the above problems?</b>
                </p>
                </div>
                <div className="row">
                <div className="col">
                    <div className="row">
                        <span className="col-2 align-self-center">Very Unsure</span>
                        <span className="col bg-secondary align-self-center">
                            <input type="text"
                                   className="col-8 slider"
                                   style={{width: "100%"}}
                                   ref={this.sliderRef} />
                        </span>
                        <span className="col-2 align-self-center">Very Sure</span>
                    </div>
                </div>
                </div>
                <div className="row mt-2">
                <div className="offset-8 col">
                    <button className="btn btn-block btn-success"
                            disabled={!!this.props.dx_certainty}
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

export default connect(mapStateToProps)(DiagnosisCertaintyControls);
