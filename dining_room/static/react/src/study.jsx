import React from 'react';
import {hot} from 'react-hot-loader';

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';


class TestComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            link: props.links[0],
            video_playing: false
        };
    }

    toggle() {
        let idx = this.props.links.indexOf(this.state.link);
        this.setState({ link: this.props.links[(idx+1) % this.props.links.length] });
    }

    playing() {
        this.setState({ video_playing: true });
    }

    ended() {
        this.setState({ video_playing: false });
    }

    render() {
        return (
            <Container fluid={true}>
            <Row>
                <Col>
                <video autoPlay={true}
                       muted={true}
                       crossOrigin="anonymous"
                       className="img-fluid"
                       key={this.state.link}
                       onPlay={this.playing.bind(this)}
                       onEnded={this.ended.bind(this)}>
                    <source src={this.state.link} />
                </video>
                </Col>
                <Col>
                    <Row>
                    <Col as="p">
                        The video is {!!this.state.video_playing ? "playing" : "stopped"}
                    </Col>
                    </Row>

                    <Row>
                    <Col>
                    <Button variant="outline-primary" block={true} onClick={this.toggle.bind(this)}>Toggle</Button>
                    </Col>
                    </Row>
                </Col>
            </Row>
            </Container>
        );
    }
}

export default hot(module)(TestComponent);
