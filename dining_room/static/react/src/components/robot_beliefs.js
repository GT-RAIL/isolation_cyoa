import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


class RobotBeliefItem extends React.Component {
    /** Each of the Belief Items */
    render() {
        let value_display = this.props.value instanceof Array
                            ? ("[ " + this.props.value.join(", ") + " ]")
                            : this.props.value;

        return (
            <tr>
                <td><i>{this.props.attr}</i></td>
                <td>{value_display}</td>
            </tr>
        );
    }
}


class RobotBeliefs extends React.Component {
    /** The robot beliefs view */
    constructor(props) {
        super(props);

        // The state definition
        this.state = {
            beliefs: [
                { attr: "Location", value: "Dining Table" },
                { attr: "Object in gripper", value: "Empty" },
                { attr: "Objects in view", value: ["Jug, Bowl"] },
                { attr: "Arm status", value: "Not moving" }
            ]
        }
    }

    render() {
        let belief_items = []
        for (const [idx, belief] of this.state.beliefs.entries()) {
            belief_items.push(<RobotBeliefItem {...belief} key={belief.value} />);
        }

        return (
            <div className="row">
            <p className="col">
                <OverlayTrigger placement="right" overlay={<Tooltip>The robot's knowledge, which may be incorrect</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Robot Beliefs</b>
            </p>
            <div className="col-10">
                <table className="table-sm table table-borderless table-hover">
                    <colgroup>
                        <col width="35%" />
                        <col width="65%" />
                    </colgroup>
                    <tbody>
                    {belief_items}
                    </tbody>
                </table>
            </div>
            </div>
        );
    }
}

export default RobotBeliefs;
export { RobotBeliefItem };
