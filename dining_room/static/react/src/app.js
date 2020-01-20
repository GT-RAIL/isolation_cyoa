import React from 'react';
import { connect } from 'react-redux';

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
        scenario_completed: state.scenario_state.scenario_completed,
        video_loaded: state.ui_status.video_loaded,
        video_playing: state.ui_status.video_playing
    };
};


/** The main app for the videos and the scenario */
let App = (props) => {
    // If the video is done playing and the state has the scenario as completed,
    // send the completion event
    let show_completion = false;
    if (!!props.video_loaded && !props.video_playing) {
        show_completion = props.scenario_completed;
    }

    return (
        <div className="container-fluid">

        {/* The modal dialog for when the study is complete */}
        <CompletionModal show={show_completion} />

        {/* The actual study UI */}
        <div className="row mt-3">
        <div className="col">
            <RobotState />
            <hr />
            <Suggestions {...props.condition} />
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
export default connect(mapStateToProps)(App);
