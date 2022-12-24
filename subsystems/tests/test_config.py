import sys
from textwrap import dedent
import fastapi

from rocketry import Rocketry
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import uvicorn
from subsystems.config import Config
from subsystems.systems import Server, Subsystems
from subsystems.utils.modules import load_instance

def test_fastapi():
    sys = Config.parse(
        {
            "apps": {
                "backend": {
                    "app": {
                        "type": "fastapi.FastAPI",
                        "description": "My app"
                    },
                    "server": {
                        "type": "uvicorn.Server",
                        "workers": 1
                    }
                }
            }
        }
    )
    assert isinstance(sys, Subsystems)

    serv = sys["backend"]
    assert isinstance(serv, Server)
    assert isinstance(serv.app, FastAPI)
    assert isinstance(serv.server, uvicorn.Server)

    assert serv.server.config.app is serv.app
    assert serv.server.config.app.description == "My app"
    assert serv.server.config.workers == 1

def test_custom_fastapi(tmpdir, request):
    orig_paths = sys.path.copy()
    test_name = request.node.originalname
    module_name = f"config_{test_name}"
    try:
        sys.path.append(str(tmpdir))
        file = tmpdir.mkdir("mydir").join(f"{module_name}.py")
        file.write(dedent("""
        from fastapi import FastAPI
        myapp = FastAPI(description="Myapplication")
        """))
        systems = Config.parse(
            {
                "apps": {
                    "backend": {
                        "app": {
                            "instance": f"mydir.{module_name}:myapp",
                        },
                        "server": {
                            "type": "uvicorn.Server",
                            "workers": 1
                        }
                    }
                }
            }
        )
        assert isinstance(systems, Subsystems)

        serv = systems["backend"]
        assert isinstance(serv, Server)
        assert isinstance(serv.app, FastAPI)
        assert isinstance(serv.server, uvicorn.Server)
        assert serv.server.config.app.description == "Myapplication"
    finally:
        sys.path = orig_paths

def test_static_app(tmpdir):
    with tmpdir.as_cwd():
        file = tmpdir.mkdir("mydir").join("mycontent.html")
        static_file = tmpdir.mkdir("static").join("mycss.css")
        file.write("<h1>Hello world!</h1>")
        static_file.write("h1 {\n  text-color: blue\n}")

        systems = Config.parse(
            {
                "apps": {
                    "backend": {
                        "app": {
                            "type": "subsystems.apps.StaticApp",
                            "path": "mydir/mycontent.html",
                            "static_path": str(tmpdir),
                            "description": "My app",
                        },
                        "server": {
                            "type": "uvicorn.Server",
                            "workers": 1
                        }
                    }
                }
            }
        )
        assert isinstance(systems, Subsystems)

        app = systems["backend"].app
        assert app.description == "My app"

        client = TestClient(app)
        assert client.get("/").text == "<h1>Hello world!</h1>"
        assert client.get("/static/mycss.css").text.replace("\r", "") == "h1 {\n  text-color: blue\n}"

def test_scheduler(tmpdir, request):
    orig_paths = sys.path.copy()
    test_name = request.node.originalname
    module_name = f"config_{test_name}"
    try:
        sys.path.append(str(tmpdir))
        file = tmpdir.mkdir(f"mydir").join(f"{module_name}.py")
        file.write(dedent("""
        from rocketry import Rocketry
        myapp = Rocketry(execution="main")
        """))

        systems = Config.parse(
            {
                "apps": {
                    "backend": {
                        "app": {
                            "instance": f"mydir.{module_name}:myapp"
                        }
                    }
                }
            }
        )
        assert isinstance(systems, Subsystems)

        app = systems["backend"].app
        assert isinstance(app, Rocketry)
        assert app.session.config.execution == "main"
    finally:
        sys.path = orig_paths

def test_cluster(tmpdir, request):
    orig_paths = sys.path.copy()
    test_name = request.node.originalname
    module_sched = f"config_{test_name}_sched"
    module_api = f"config_{test_name}_api"
    try:
        sys.path.append(str(tmpdir))
        app_dir = tmpdir.mkdir(f"mydir")

        file = app_dir.join(f"{module_sched}.py")
        file.write(dedent("""
        from rocketry import Rocketry
        myapp = Rocketry(execution="main")
        """))

        file = app_dir.join(f"{module_api}.py")
        file.write(dedent("""
        from fastapi import FastAPI
        myapp = FastAPI()
        """))

        systems = Config.parse(
            {
                "apps": {
                    "backend": {
                        "app": {
                            "type": "subsystems.apps.ClusterApp",
                            "api": {
                                "app": {
                                    "instance": f"mydir.{module_api}:myapp"
                                },
                                "server": {
                                    "type": "uvicorn.Server",
                                }
                            },
                            "scheduler": {
                                "app": {
                                    "instance": f"mydir.{module_sched}:myapp"
                                },
                            },
                        }
                    }
                }
            }
        )
        assert isinstance(systems, Subsystems)

        backend = systems["backend"]
        assert backend.server.apps.keys() == {"scheduler", "api"}
        assert isinstance(backend.server.apps["api"].app, FastAPI)
        assert isinstance(backend.server.apps["scheduler"].app, Rocketry)
        #app = systems["backend"].app
        #assert isinstance(app, Rocketry)
        #assert app.session.config.execution == "main"
    finally:
        sys.path = orig_paths

@pytest.mark.parametrize("server,app,server_cls,app_cls", [
    pytest.param("uvicorn", "FastAPI", "uvicorn.Server", "fastapi.FastAPI", id="uvicorn (FastAPI)"), 
    pytest.param("waitress", "Flask", "waitress.server.MultiSocketServer", "flask.Flask", id="waitress (Flask)"),
    pytest.param("werkzeug", "Flask", "werkzeug.serving.BaseWSGIServer", "flask.Flask", id="werkzeug (Flask)"),
    pytest.param(None, "Rocketry", "rocketry.Rocketry", "rocketry.Rocketry", id="rocketry"),
])
def test_aliases(server, app, server_cls, app_cls):
    if server is None:
        systems = Config.parse(
            {
                "apps": {
                    "myapp": {
                        "app": {
                            "type": app,
                            "import_name": __name__
                        },
                    }
                }
            }
        )
    else:
        systems = Config.parse(
            {
                "apps": {
                    "myapp": {
                        "app": {
                            "type": app,
                            "import_name": __name__
                        },
                        "server": {
                            "type": server,
                            "host": "localhost",
                            "port": 8080
                        }
                    }
                }
            }
        )
    assert isinstance(systems['myapp'].server, load_instance(server_cls))
    assert isinstance(systems['myapp'].app, load_instance(app_cls))