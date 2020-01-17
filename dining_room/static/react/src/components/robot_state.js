import React from 'react';

import RobotVideo from './robot_video';
import RobotBeliefs from './robot_beliefs';


class RobotState extends React.Component {
    /** The robot state view */
    render() {
        return (
            <div className="row">
            <div className="col">
                <RobotVideo />
                <div className="my-3" />
                <RobotBeliefs />
            </div>
            </div>
        );
    }
}

export default RobotState;
