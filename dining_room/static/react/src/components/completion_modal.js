import React from 'react';
import Modal from 'react-bootstrap/Modal';


/** The modal when the study is complete */
class CompletionModal extends React.Component {
    render() {
        return (
            <Modal show={this.props.show} size="lg" centered onHide={() => {}}>
            <Modal.Header>
                <Modal.Title>Complete!</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <p>The connection with the robot is now severed. Please click the button below to continue with the study.</p>
            </Modal.Body>
            <Modal.Footer>
                <a href={window.constants.NEXT_URL} role="button" className="btn btn-primary">Continue</a>
            </Modal.Footer>
            </Modal>
        );
    }
}

export default CompletionModal;
