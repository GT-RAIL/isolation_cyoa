import './css/styles.scss';

import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import { createLogger } from 'redux-logger';

import App from './src/app';
import AppState from './src/reducers';

const loggerMiddleware = createLogger();
const store = createStore(AppState, {}, applyMiddleware(thunkMiddleware, loggerMiddleware));

ReactDOM.render(
    <Provider store={store}>
        <App condition={window.constants.EXPERIMENT_CONDITION} />
    </Provider>,
    document.getElementById("app")
);
