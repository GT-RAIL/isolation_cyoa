import React from 'react';
import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle } from '@fortawesome/free-regular-svg-icons/faTimesCircle';
import { faCheckCircle } from '@fortawesome/free-regular-svg-icons/faCheckCircle';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

class HistoryItem extends React.Component {
    /** Each item in the shown history */
    render() {
        let error_display = this.props.error instanceof Array
                            ? this.props.error.map((err) => <span key={err}>{err}<br/></span>)
                            : this.props.error;
        let result_display = !!this.props.result
                             ? <h5 className="text-success"><FontAwesomeIcon icon={faCheckCircle} /></h5>
                             : <h5 className="text-danger"><FontAwesomeIcon icon={faTimesCircle} /></h5>;

        return (
            <table className="table-sm table text-center">
                <colgroup>
                    <col width="10%" />
                    <col width="50%" />
                    <col width="30%" />
                    <col width="10%" />
                </colgroup>
                <thead className="thead-light">
                <tr>
                    <th scope="col">#</th>
                    <th scope="col">Errors Present</th>
                    <th scope="col">Action Taken</th>
                    <th scope="col">Result</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <th scope="row">{this.props.idx}</th>
                    <td>{error_display}</td>
                    <td>{this.props.action}</td>
                    <td>{result_display}</td>
                </tr>
                </tbody>
            </table>
        );
    }
}


class History extends React.Component {
    /** The history view */
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "350px";

        // The state definition
        this.state = {
            history: [
                { error: ["Something was wrong"], action: "An action", result: true },
                { error: ["Something else was wrong", "Something was wrong"], action: "Another action", result: true },
                { error: ["Unknown"], action: "Yet another action", result: false },
                { error: ["Something was wrong"], action: "An action", result: true },
                { error: ["It was wrong", "Something was wrong"], action: "Another action", result: true },
                { error: ["Unknown", "Something very wrong"], action: "Yet another action", result: false }
            ]
        };
    }

    render() {
        let history_items = [];
        for (const [idx, history] of this.state.history.slice().reverse().entries()) {
            history_items.push(
                <div className="row" key={this.state.history.length-idx}>
                <div className="col">
                    <HistoryItem idx={this.state.history.length-idx} {...history} />
                </div>
                </div>
            );
        }

        return (
            <div className="row overflow-auto" style={{ maxHeight: this.MAX_HEIGHT }}>
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>The history of actions you have taken, the most-recent first</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>History</b>
                </p>
                </div>
                <div className="row">
                <div className="col">
                    {history_items}
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default History;
export { HistoryItem };
