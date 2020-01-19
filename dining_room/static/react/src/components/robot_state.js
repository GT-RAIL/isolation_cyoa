import React from 'react';

import RobotVideo from './robot_video';
import RobotBeliefs from './robot_beliefs';


/** The robot state view */
class RobotState extends React.Component {
    render() {
        return (
            <div className="row">
            <div className="col">
                <RobotVideo />
                <div className="my-3" />
                <RobotBeliefs video_status={this.props.video_status} />
            </div>
            </div>
        );
    }
}

export default RobotState;
