import './css/styles.scss';

import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import { createLogger } from 'redux-logger';
import { hot } from 'react-hot-loader/root';

import App from './src/app';
import AppState from './src/reducers';

const loggerMiddleware = createLogger();
const store = createStore(AppState, {}, applyMiddleware(thunkMiddleware, loggerMiddleware));


// Root component that we connect the store to as well as HMR, etc.
let Root = (props) => {
    return (
        <Provider store={store}>
            <App condition={window.constants.EXPERIMENT_CONDITION} />
        </Provider>
    );
};

Root = hot(Root);


ReactDOM.render(<Root />, document.getElementById("app"));
