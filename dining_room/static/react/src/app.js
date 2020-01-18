import React from 'react';
import {hot} from 'react-hot-loader/root';

// Import the top-level components
import RobotState from './components/robot_state';
import Suggestions from './components/suggestions';
import Goals from './components/goals';
import History from './components/history';
import Controls from './components/controls';
import CompletionModal from './components/completion_modal';


class App extends React.Component {
    /** The main app for the videos and the scenario */
    constructor(props) {
        super(props);
        this.state = {
            scenario_completed: false,
            video_status: {
                video_loaded: false,
                video_playing: false
            }
        };
    }

    render() {
        return (
            <div className="container-fluid">

            {/* The modal dialog for when the study is complete */}
            <CompletionModal show={this.state.scenario_completed} />

            {/* The actual study UI */}
            <div className="row mt-3">
            <div className="col">
                <RobotState video_status={this.state.video_status} />
                <hr />
                <Suggestions video_status={this.state.video_status} {...this.props.condition} />
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
            <button className="fixed-bottom btn btn-secondary" onClick={() => { this.setState({ scenario_completed: true }) } }>Toggle Completion</button>
            </div>
            </div>
        );
    }
}

export default hot(App);
