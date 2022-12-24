import asyncio
import signal
from typing import Dict, List, Type, Union

from subsystems.utils.modules import load_instance

def create_server(cls_name:str, **kwargs) -> 'ServerBase':
    try:
        cls = get_server_class(cls_name)
    except KeyError:
        return load_instance(cls_name)(**kwargs)
    else:
        return cls(**kwargs)

def get_server_class(cls_name):
    if cls_name is None:
        return DummyServer
    return ServerBase._cls_servers[cls_name]


def register_server(cls, aliases:List[str]):
    for alias in aliases:
        ServerBase._cls_servers[alias] = cls

class ServerBase:
    "Abstracted server"

    use_instance = False
    use_import_path = False

    _cls_servers: Dict[str, 'ServerBase'] = {}

    def __init__(self, *, app_instance=None, app_path:str=None, config:dict=None):
        self.app_instance = app_instance
        self.app_path = app_path
        self.config = config

        self.instance = self.create()
        if hasattr(self.app_instance, "add_server"):
            self.app_instance.add_server(self.instance)

    def create(self):
        ...

    async def serve(self, *args, **kwargs):
        server = self.instance
        await server.serve(*args, **kwargs)

    def run(self, *args, **kwargs):
        server = self.instance
        if hasattr(server, "run"):
            server.run(*args, **kwargs)
        elif hasattr(server, "serve_forever"):
            server.serve_forever(*args, **kwargs)
        else:
            asyncio.run(self.serve(*args, **kwargs))

    def handle_exit(self, *args, **kwargs):
        ...

class DummyServer(ServerBase):
    "Server that's actually just serving the app"
    use_instance = True
    use_import_path = False

    def create(self):
        return self.app_instance

# FastAPI Servers
# ---------------

class UvicornServer(ServerBase):
    use_instance = True
    use_import_path = True

    def create(self):
        import uvicorn 
        return uvicorn.Server(uvicorn.Config(app=self.app_instance, **self.config))

    def handle_exit(self, *args, **kwargs):
        self.instance.handle_exit(*args, **kwargs)

class HypercornServer(ServerBase):
    use_instance = False
    use_import_path = True

    def run(self):
        from hypercorn.run import run
        return run(application=self.app_path, **self.config)

    def handle_exit(self, *args, **kwargs):
        self.instance.close(*args, **kwargs)

# Flask Servers
# -------------

class WaitressServer(ServerBase):
    use_instance = True
    use_import_path = True

    def create(self):
        import waitress
        return waitress.create_server(application=self.app_instance, **self.config)

    def handle_exit(self, *args, **kwargs):
        self.instance.close(*args, **kwargs)

class WerkzeugServer(ServerBase):
    use_instance = True
    use_import_path = True

    def create(self):
        import werkzeug
        return werkzeug.serving.make_server(app=self.app_instance, **self.config)

    def handle_exit(self, *args, **kwargs):
        self.instance.shutdown(*args, **kwargs)

# Hybrid Servers
# --------------

class GunicornServer(ServerBase):
    use_instance = True
    use_import_path = True

    def create(self):
        from subsystems.extensions.gunicorn import GunicornApplication
        return GunicornApplication(app_uri=self.app_path, **self.config)

    def handle_exit(self, *args, **kwargs):
        signal.raise_signal(signal.SIGINT)

register_server(UvicornServer, aliases=["uvicorn", "uvicorn.Server"])
register_server(WaitressServer, aliases=["waitress", "waitress.create_server"])
register_server(HypercornServer, aliases=["hypercorn", "hypercorn.run.run"])
register_server(WerkzeugServer, aliases=["werkzeug", "werkzeug.serving.make_server"])
register_server(GunicornServer, aliases=["gunicorn"])
