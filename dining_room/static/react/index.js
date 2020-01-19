import './css/styles.scss';

import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore } from 'redux';

import App from './src/app';
import AppState from './src/reducers';

const store = createStore(AppState);

ReactDOM.render(
    <Provider store={store}>
        <App condition={window.constants.EXPERIMENT_CONDITION} />
    </Provider>,
    document.getElementById("app")
);
