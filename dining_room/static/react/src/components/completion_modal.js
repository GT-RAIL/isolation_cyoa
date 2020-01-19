import React from 'react';
import Modal from 'react-bootstrap/Modal';


/** The modal when the study is complete */
const CompletionModal = (props) => {
    return (
        <Modal show={props.show} size="lg" centered onHide={() => {}}>
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

export default CompletionModal;
