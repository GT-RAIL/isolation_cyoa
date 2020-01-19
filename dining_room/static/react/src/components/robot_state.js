import React from 'react';

import RobotVideo from './robot_video';
import RobotBeliefs from './robot_beliefs';


/** The robot state view */
let RobotState = (props) => {
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

export default RobotState;
