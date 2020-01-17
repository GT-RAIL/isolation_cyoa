import React from 'react';


class ActionControlButton extends React.Component {
    render() {
        return (
            <button className="btn btn-outline-info btn-block" style={{height: "100%"}}>{this.props.name}</button>
        );
    }
}


class ActionControls extends React.Component {
    /** The action controls view */
    constructor(props) {
        super(props);

        // Constants
        this.NUMBER_BUTTONS_PER_ROW = 2;

        // The state definition
        this.state = {
            valid_actions: [
                { name: "This is an action", value: 'action-1' },
                { name: "This is another action", value: 'action-2' },
                { name: "Yet another action with a long name", value: 'action-3' },
                { name: "This is an action", value: 'action-4' },
                { name: "This is another action", value: 'action-5' },
                { name: "Yet another action", value: 'action-6' },
                { name: "This is an action that also has a long name", value: 'action-7' },
                { name: "This is another action", value: 'action-8' },
                { name: "Yet another action", value: 'action-9' }
            ]
        };
    }

    render() {
        let action_buttons = [];
        let sublist = [];
        for (const [idx, action]of this.state.valid_actions.entries()) {
            sublist.push(
                <div className="col"><ActionControlButton {...action} key={action.value} /></div>
            );

            // We want to close off after every sublist has x elements
            if ((sublist.length % this.NUMBER_BUTTONS_PER_ROW) === 0) {
                action_buttons.push(
                    <div className="row my-1" key={idx}>{sublist}</div>
                );
                sublist = [];
            }
        }
        // const action_buttons = this.state.valid_actions.map(
        //     (action) => <ActionControlButton {...action} key={action.value} />
        // );

        return (
            <div className="row">
            <div className="col">
                {action_buttons}
            </div>
            </div>
        );
    }
}

export default ActionControls;
export { ActionControlButton };
