import React from 'react';


class HistoryItem extends React.Component {
    /** Each item in the shown history */
    render() {
        return (
            <table className="table-sm table-responsive">
                <col width="60%" />
                <col width="30%" />
                <col width="10%" />
                <thead className="thead-dark">
                <tr>
                    <th scope="col">Errors Present</th>
                    <th scope="col">Action Taken</th>
                    <th scope="col">Result</th>
                </tr>
                </thead>
            </table>
        );
    }
}


class History extends React.Component {
    /** The history view */
    constructor(props) {
        super(props);

        // Constants
        this.MAX_HEIGHT = "35%";

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
        }
    }

    render() {
        return (
            <div className="row" style={{ maxHeight: this.MAX_HEIGHT }}>
                <div className="col"><HistoryItem /></div>
            </div>
        );
    }
}

export default History;
export { HistoryItem };
