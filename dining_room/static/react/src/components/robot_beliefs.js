import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';


/** Each of the Belief Items */
class RobotBeliefItem extends React.Component {
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


/** The robot beliefs view */
class RobotBeliefs extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.SHOW_IN_VIDEO_ATTRS = ["Arm status"];

        // The state definition
        this.state = {
            beliefs: [
                { attr: "Location", value: "Dining Table" },
                { attr: "Object in gripper", value: "Empty" },
                { attr: "Objects in view", value: ["Jug, Bowl"] },
                { attr: "Arm status", value: "In motion" }
            ]
        }
    }

    shouldShowAttr(video_status, attr) {
        /* Determine if the attribute should be displayed */
        if (!video_status || !video_status.video_loaded) {
            return false;
        }
        else {
            return (
                (!!video_status.video_playing && this.SHOW_IN_VIDEO_ATTRS.includes(attr))
                || (!video_status.video_playing && !this.SHOW_IN_VIDEO_ATTRS.includes(attr))
            );
        }
    }

    render() {
        let belief_items = []
        for (const [idx, belief] of this.state.beliefs.entries()) {
            if (this.shouldShowAttr(this.props.video_status, belief.attr)) {
                belief_items.push(<RobotBeliefItem {...belief} key={belief.value} />);
            }
        }

        return (
            <div className="row">
            <p className="col">
                <OverlayTrigger placement="right" overlay={<Tooltip>The robot's knowledge, which may be incorrect</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>Robot Beliefs</b>
            </p>
            <div className="col-9">
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
