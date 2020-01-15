var Container = ReactBootstrap.Container;
var Row = ReactBootstrap.Row;
var Col = ReactBootstrap.Col;
var Button = ReactBootstrap.Button;


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

ReactDOM.render(<TestComponent links={["https://dl.dropboxusercontent.com/s/mf385zlxfoyqtb8/kc.kc.gripper.gripper.gripper.look_at_dt.mp4", "https://dl.dropboxusercontent.com/s/p144ik18262tjw9/dt.kc.occluding.default.default.look_at_kc.mp4"]} />, document.getElementById("app"));
