from pathlib import Path
import sys
from textwrap import dedent
import uuid
import signal
import pytest
from subsystems.main_cli import parse_args, main
import subsystems

@pytest.mark.parametrize("args,output",
    [
        pytest.param(["init", 'rocketry'], {
            'command':'init',
            'template': 'rocketry',
        }, id="init (defaults)"),
        pytest.param(["launch", '--config', 'myconf.yaml'], {
            'command': 'launch', 
            'app': [],
            'template': None,
            'config': 'myconf.yaml',
        }, id="launch (config)"),
        pytest.param(["launch", '--template', 'rocketry'], {
            'command': 'launch', 
            'app': [],
            'template': 'rocketry',
            'config': None,
        }, id="launch (template)"),
        pytest.param(["launch", 'frontend', '--template', 'rocketry'], {
            'command': 'launch', 
            'app': ['frontend'],
            'template': 'rocketry',
            'config': None,
        }, id="launch (specific app)"),
        pytest.param(["launch", 'frontend', 'backend', '--template', 'rocketry'], {
            'command': 'launch', 
            'app': ['frontend', 'backend'],
            'template': 'rocketry',
            'config': None,
        }, id="launch (specific apps)"),
        pytest.param(["launch", '--template', 'rocketry', '--host-back', '0.0.0.0', '--port-back', '8080'], {
            'command': 'launch', 
            'app': [],
            'template': 'rocketry',
            'config': None,
            'host_back': '0.0.0.0',
            'port_back': '8080',
        }, id="launch (arbitrary params)"),
    ]
)
def test_parser(args, output):
    args = parse_args(args)
    assert vars(args) == output

def test_init(tmpdir):
    root = subsystems.__file__
    with tmpdir.as_cwd():
        main(["init", "rocketry"])
        assert Path(tmpdir / "subsystems.yaml").is_file()
        assert Path(tmpdir / "subsystems.yaml").read_text() == (Path(root).parent / "templates" / "rocketry.yaml").read_text()

@pytest.mark.parametrize("how", [
    pytest.param("template", id="use template"),
    pytest.param("init", id="use init")
])
def test_launch(tmpdir, tmpsyspath, how):
    tmpsyspath.append(str(tmpdir))
    mdl_name = uuid.uuid4().hex
    sched_file = tmpdir.join(f"{mdl_name}.py")
    sched_file.write(dedent("""
        import signal
        from pathlib import Path
        from rocketry import Rocketry
        from rocketry.conds import true, scheduler_cycles
        app = Rocketry()
        app.session.config.shut_cond = scheduler_cycles(1)

        @app.task(true)
        def do_things():
            Path("status.txt").write_text("Did run")

        @app.task(on_shutdown=True)
        def cause_interupt():
            signal.raise_signal(signal.SIGINT)

    """))

    with tmpdir.as_cwd():
        if how == "template":
            main(["launch", "--template", "rocketry", "--scheduler", f"{mdl_name}:app"])
        elif how == "init":
            main(["init", "rocketry"])
            main(["launch", "--scheduler", f"{mdl_name}:app"])
        assert Path("status.txt").is_file()