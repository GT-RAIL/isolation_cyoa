import './css/styles.scss';

import React from 'react';
import ReactDOM from 'react-dom';

import TestComponent from './src/study';

ReactDOM.render(<TestComponent links={
    ["https://dl.dropboxusercontent.com/s/mf385zlxfoyqtb8/kc.kc.gripper.gripper.gripper.look_at_dt.mp4",
    "https://dl.dropboxusercontent.com/s/p144ik18262tjw9/dt.kc.occluding.default.default.look_at_kc.mp4"]
} />, document.getElementById("app"));
