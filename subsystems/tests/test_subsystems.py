from multiprocessing import Process
import signal
from threading import Thread
from textwrap import dedent
import sys
import uuid
from pathlib import Path

import pytest
import requests


from subsystems.config import Config
from subsystems.systems import Subsystems

@pytest.mark.parametrize("server",
    [
        'uvicorn.Server',
        'hypercorn.run.run'
    ]
)
def test_fastapi(tmpdir, request, tmpsyspath, server):
    tmpsyspath.append(str(tmpdir))
    randstr = uuid.uuid4().hex
    module_name = f"config_{randstr}"

    file = tmpdir.join(f"{module_name}.py")
    file.write(dedent("""
    from fastapi import FastAPI
    myapp = FastAPI(description="Myapplication")
    @myapp.get("/")
    def get_stuff():
        return "Hello world"
    """))
    systems = Subsystems.from_config(
        {
            "apps": {
                "backend": {
                    "app": {
                        "instance": f"{module_name}:myapp",
                        "lazy_load": True
                    },
                    "server": {
                        "type": server,
                        "workers": 1,
                        "host": "localhost",
                        "port": "8999"
                    }
                }
            }
        }
    )
    t = Thread(target=systems.run, args=())
    t.start()
    try:
        output = requests.get("http://localhost:8999/")
        assert output.status_code == 200
        assert output.text == '"Hello world"'
    finally:
        systems["backend"].handle_exit(1, None)


@pytest.mark.parametrize("server",
    [
        'werkzeug.serving.make_server',
        'waitress.create_server',
        'gunicorn',
    ]
)
def test_flask(tmpdir, request, tmpsyspath, server):
    if server.startswith("gunicorn") and sys.platform == "win32":
        pytest.skip(reason="Gunicorn not supported on Windows")
    tmpsyspath.append(str(tmpdir))
    randstr = uuid.uuid4().hex
    test_name = request.node.originalname
    module_name = f"config_{test_name}"

    file = tmpdir.mkdir("mydir").join(f"{module_name}.py")
    file.write(dedent("""
    from flask import Flask
    myapp = Flask(__name__)

    @myapp.route('/')
    def hello_world():
        return 'Hello world'
    """))

    systems = Subsystems.from_config(
        {
            "apps": {
                "backend": {
                    "app": {
                        "instance": f"mydir.{module_name}:myapp",
                    },
                    "server": {
                        "type": server,
                        'host': 'localhost',
                        'port': '8999'
                    }
                }
            }
        }
    )

    t = Thread(target=systems["backend"].run, args=())
    t.start()
    try:
        output = requests.get("http://localhost:8999/")
        assert output.status_code == 200
        assert output.text == 'Hello world'
    finally:
        systems["backend"].handle_exit()
