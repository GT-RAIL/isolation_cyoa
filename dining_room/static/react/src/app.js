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


// class TestComponent extends React.Component {
//     constructor(props) {
//         super(props);
//         this.state = {
//             link: props.links[0],
//             video_playing: false
//         };
//     }

//     toggle() {
//         let idx = this.props.links.indexOf(this.state.link);
//         this.setState({ link: this.props.links[(idx+1) % this.props.links.length] });
//     }

//     playing() {
//         this.setState({ video_playing: true });
//     }

//     ended() {
//         this.setState({ video_playing: false });
//     }

//     render() {
//         return (
//             <Container fluid={true}>
//             <Row>
//                 <Col>
//                 <video autoPlay={true}
//                        muted={true}
//                        crossOrigin="anonymous"
//                        className="img-fluid"
//                        key={this.state.link}
//                        onPlay={this.playing.bind(this)}
//                        onEnded={this.ended.bind(this)}>
//                     <source src={this.state.link} />
//                 </video>
//                 </Col>
//                 <Col>
//                     <Row>
//                     <Col as="p">
//                         The video is {!!this.state.video_playing ? "playing" : "stopped"}
//                     </Col>
//                     </Row>

//                     <Row>
//                     <Col>
//                     <Button variant="outline-primary" block={true} onClick={this.toggle.bind(this)}>Toggle</Button>
//                     </Col>
//                     </Row>
//                 </Col>
//             </Row>
//             </Container>
//         );
//     }
// }
