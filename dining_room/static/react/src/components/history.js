import React from 'react';
import { connect } from 'react-redux';

import Tooltip from 'react-bootstrap/Tooltip';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle } from '@fortawesome/free-regular-svg-icons/faTimesCircle';
import { faCheckCircle } from '@fortawesome/free-regular-svg-icons/faCheckCircle';
import { faQuestionCircle } from '@fortawesome/free-regular-svg-icons/faQuestionCircle';

/** Each item in the shown history */
class HistoryItem extends React.Component {
    render() {
        let error_display = this.props.error instanceof Array
                            ? this.props.error.map((err) => <span key={err}>{window.constants.DIAGNOSES[err]}<br/></span>)
                            : window.constants.DIAGNOSES[this.props.error];
        let result_display = !!this.props.result
                             ? <h5 className="text-success"><FontAwesomeIcon icon={faCheckCircle} /></h5>
                             : <h5 className="text-danger"><FontAwesomeIcon icon={faTimesCircle} /></h5>;

        return (
            <tr>
                <th scope="row">{this.props.idx}</th>
                <td>{error_display}</td>
                <td>{window.constants.ACTIONS[this.props.action]}</td>
                <td>{result_display}</td>
            </tr>
        );
    }
}


/** Function to get the props from the global store */
const mapStateToProps = (state, ownProps) => {
    return {
        history: state.history.history
    };
}

/** The history view */
class History extends React.Component {
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "250px";
    }

    render() {
        let history_items = [];
        for (const [idx, history] of this.props.history.slice().reverse().entries()) {
            history_items.push(
                <HistoryItem key={this.props.history.length-idx} idx={this.props.history.length-idx} {...history} />
            );
        }

        return (
            <div className="row overflow-auto" style={{ maxHeight: this.MAX_HEIGHT }}>
            <div className="col">
                <div className="row">
                <p className="col">
                    <OverlayTrigger placement="right" overlay={<Tooltip>The history of actions you have taken with the most-recent first</Tooltip>}><FontAwesomeIcon icon={faQuestionCircle} /></OverlayTrigger> <b>History</b>
                </p>
                </div>
                <div className="row">
                <div className="col">
                    <table className={"table-sm table text-center" + (history_items.length > 0 ? "" : " invisible")}>
                        <colgroup>
                            <col width="10%" />
                            <col width="40%" />
                            <col width="40%" />
                            <col width="10%" />
                        </colgroup>
                        <thead className="thead-light">
                        <tr>
                            <th scope="col">#</th>
                            <th scope="col">Problems Identified</th>
                            <th scope="col">Action Taken</th>
                            <th scope="col">Result</th>
                        </tr>
                        </thead>
                        <tbody>
                        {history_items}
                        </tbody>
                    </table>
                </div>
                </div>
            </div>
            </div>
        );
    }
}

export default connect(mapStateToProps)(History);
export { HistoryItem };
