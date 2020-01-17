import React from 'react';


class Goals extends React.Component {
    /** The goal view */
    render() {
        return (
            <div className="row">
            <div className="col">
                <p style={{"marginBottom": 0}}>The robot's goal is to <b>Pick the Mug</b></p>
                <p style={{"marginBottom": 0}} className="text-center">from the <b>Kitchen Counter</b></p>
                <p style={{"marginBottom": 0}} className="text-right">and take it to the <b>Couch</b>.</p>
            </div>
            </div>
        );
    }
}

export default Goals;
