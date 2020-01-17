import React from 'react';


class RobotVideo extends React.Component {
    /** The robot video view */
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "640px";

        // FIXME: Placeholder video link
        this.VIDEO_LINK = "https://dl.dropboxusercontent.com/s/mf385zlxfoyqtb8/kc.kc.gripper.gripper.gripper.look_at_dt.mp4";

        // The state definition
        this.state = {
            video_playing: false
        }
    }

    ended() {
        this.setState({ video_playing: false });
    }

    playing() {
        this.setState({ video_playing: true });
    }

    render() {
        return (
            <div className="row">
            <div className="col">
                <div className="embed-responsive embed-responsive-4by3" style={{ maxHeight: this.MAX_HEIGHT }}>
                    <video autoPlay={true}
                           muted={true}
                           className="embed-responsive-item"
                           key={this.VIDEO_LINK}
                           onPlay={this.playing.bind(this)}
                           onEnded={this.ended.bind(this)}>
                        <source src={this.VIDEO_LINK} />
                    </video>
                </div>
            </div>
            </div>
        );
    }
}

export default RobotVideo;
