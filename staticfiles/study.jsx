var Container = ReactBootstrap.Container;
var Row = ReactBootstrap.Row;
var Col = ReactBootstrap.Col;

class TestComponent extends React.Component {
    render() {
        return (
            <Container fluid={true}>
                <Row>
                    <Col>
                        <video autoPlay={true} muted={true} crossOrigin="anonymous" className="img-fluid">
                        <source src="https://dl.dropboxusercontent.com/s/800xgr10vkm9v3j/kc.kc.default.gripper.default.look_at_dt.mp4" />
                        </video>
                    </Col>
                </Row>
            </Container>
        );
    }
}

ReactDOM.render(<TestComponent name="banerjs" />, document.getElementById("app"));
