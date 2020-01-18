import './css/styles.scss';

import React from 'react';
import ReactDOM from 'react-dom';

import App from './src/app';

ReactDOM.render(<App condition={window.constants.EXPERIMENT_CONDITION} />, document.getElementById("app"));
