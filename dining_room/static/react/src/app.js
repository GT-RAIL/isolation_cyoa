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
            show_completion: false
        };
    }

    render() {
        return (
            <div className="container-fluid">

            {/* The modal dialog for when the study is complete */}
            <CompletionModal show={this.state.show_completion} />

            {/* The actual study UI */}
            <div className="row mt-3">
            <div className="col">
                <RobotState />
                <hr />
                <Suggestions />
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
            <button className="fixed-bottom btn btn-secondary" onClick={() => { this.setState({ show_completion: true }) } }>Toggle Completion</button>
            </div>
            </div>
        );
    }
}

export default hot(App);
