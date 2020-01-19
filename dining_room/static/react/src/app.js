import React from 'react';
import { connect } from 'react-redux';
import { hot } from 'react-hot-loader/root';

// Import the top-level components
import RobotState from './components/robot_state';
import Suggestions from './components/suggestions';
import Goals from './components/goals';
import History from './components/history';
import Controls from './components/controls';
import CompletionModal from './components/completion_modal';

// Import actions
import { completeScenario } from './actions';


/** Function to get the state from the store */
const mapStateToProps = (state, ownProps) => {
    return {
        scenario_completed: state.ui_status.scenario_completed,
        video_status: {
            video_loaded: state.ui_status.video_loaded,
            video_playing: state.ui_status.video_playing
        }
    };
};


/** Callbacks to update the store */
const mapDispatchToProps = (dispatch, ownProps) => {
    return {
        onCompletionClick: (e) => {
            dispatch(completeScenario());
        }
    };
};


/** The main app for the videos and the scenario */
let App = (props) => {
    return (
        <div className="container-fluid">

        {/* The modal dialog for when the study is complete */}
        <CompletionModal show={props.scenario_completed} />

        {/* The actual study UI */}
        <div className="row mt-3">
        <div className="col">
            <RobotState video_status={props.video_status} />
            <hr />
            <Suggestions video_status={props.video_status} {...props.condition} />
        </div>
        <div className="col">
            <Goals />
            <hr />
            <History />
            <hr />
            <Controls />
        </div>
        </div>
        <div className="row">
        <button className="fixed-bottom btn btn-secondary" onClick={props.onCompletionClick}>Toggle Completion</button>
        </div>
        </div>
    );
}


// Export as a Redux wrapped component
App = connect(mapStateToProps, mapDispatchToProps)(App);


// Export as a hot-loaded component
export default hot(App);
