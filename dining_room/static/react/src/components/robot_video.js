import React from 'react';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons/faSpinner';


/** The robot video view */
class RobotVideo extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "600px";
        this.PLAY_TIMEOUT = 500;  // play X ms after the video is loaded

        // The state definition
        this.state = {
            video_link: "https://dl.dropboxusercontent.com/s/mf385zlxfoyqtb8/kc.kc.gripper.gripper.gripper.look_at_dt.mp4",

            // These are actually app-wide properties that are updated by events
            // in this component
            video_playing: false,
            video_loaded: false,
        }

        // Refs
        this.videoRef = React.createRef();
    }

    ended() {
        this.setState({ video_playing: false });
    }

    playing() {
        this.setState({ video_playing: true });
    }

    loaded() {
        this.setState({ video_loaded: true });
        setTimeout(() => { this.videoRef.current.play(); }, this.PLAY_TIMEOUT);
    }

    render() {
        return (
            <div className="row">
            <div className="col">
                <div className="view">
                    <div className={"embed-responsive embed-responsive-4by3" + (!!this.state.video_loaded ? " visible" : " invisible")} style={{ maxHeight: this.MAX_HEIGHT }}>
                        <video autoPlay={false}
                               muted={true}
                               className="embed-responsive-item"
                               key={this.state.video_link}
                               onPlay={this.playing.bind(this)}
                               onEnded={this.ended.bind(this)}
                               onCanPlayThrough={this.loaded.bind(this)}
                               ref={this.videoRef}>
                            <source src={this.state.video_link} />
                        </video>
                    </div>
                    <div className={"mask text-center" + (!this.state.video_loaded ? "" : " d-none")}>
                        <h1 className="mb-5">Communicating with robot...</h1>
                        <p className="text-primary"><FontAwesomeIcon icon={faSpinner} size="9x" pulse /></p>
                    </div>
                </div>
            </div>
            </div>
        );
    }
}

export default RobotVideo;
