import React from 'react';
import { connect } from 'react-redux';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons/faSpinner';

// Import actions
import { playVideo, displayState } from '../actions';


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        video_link: state.scenario_state.video_link,
        video_loaded: state.ui_status.video_loaded,
        ax_selected_time: state.ui_status.ax_selected_time
    };
}


/** The robot video view */
class RobotVideo extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "600px";
        this.PLAY_TIMEOUT = 500;  // play X ms after the video is loaded

        // Bind the functions
        this.loaded = this.loaded.bind(this);
        this.ended = this.ended.bind(this);

        // Refs
        this.videoRef = React.createRef();
    }

    ended() {
        this.props.dispatch(displayState());
    }

    loaded() {
        if (!this.props.video_loaded) {
            this.props.dispatch(playVideo());
            setTimeout(() => { this.videoRef.current.play(); }, this.PLAY_TIMEOUT);
        }
    }

    render() {
        return (
            <div className="row">
            <div className="col">
                <div className="view">
                    <div className={"embed-responsive embed-responsive-4by3" + ((!this.props.ax_selected_time && !!this.props.video_loaded) ? " visible" : " invisible")}
                         style={{ maxHeight: this.MAX_HEIGHT }}
                         key={this.props.video_loaded || !!this.props.ax_selected_time}>
                        <video autoPlay={false}
                               muted={true}
                               className="embed-responsive-item"
                               key={this.props.video_link}
                               onEnded={this.ended}
                               onCanPlayThrough={this.loaded}
                               ref={this.videoRef}>
                            <source src={this.props.video_link} />
                        </video>
                    </div>
                    <div className={"mask text-center" + ((!!this.props.ax_selected_time || !this.props.video_loaded) ? "" : " d-none")}>
                        <h1 className="mb-5">Communicating with robot...</h1>
                        <p className="text-primary"><FontAwesomeIcon icon={faSpinner} size="9x" pulse /></p>
                    </div>
                </div>
            </div>
            </div>
        );
    }
}


// Export as a wrapped Redux component
export default connect(mapStateToProps)(RobotVideo);
