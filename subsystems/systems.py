import asyncio
import threading
import signal
from typing import Dict, Type, Union

from subsystems.utils.modules import load_instance

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)



class Server:
    "Abstracted server"

    def __init__(self, app, cls:Type=None, config:dict=None):
        self.app = app
        self.cls = cls
        self.config = config

        self.server = self.get_server()

    def get_server(self):
        if self._is_instance("uvicorn.Server"):
            import uvicorn
            return self.cls(uvicorn.Config(app=self.app, **self.config))
        elif self._is_instance("hypercorn.run.run"):
            import hypercorn
            return self.cls(hypercorn.Config.from_mapping(application_path=self.app, **self.config))
        elif self._is_instance("waitress.create_server"):
            return self.cls(application=self.app, **self.config)
        elif self.cls is None:
            # Expecting the app can run itself
            return self.app
        return self.cls(app=self.app, **self.config)

    def _is_instance(self, mdl):
        try:
            return self.cls is load_instance(mdl)
        except ImportError:
            return False

    def _is_hypercorn(self):
        try:
            from hypercorn.run import run as run_hypercorn
            return self.cls is run_hypercorn
        except ImportError:
            return False

    async def serve(self, *args, **kwargs):
        server = self.server
        await server.serve(*args, **kwargs)

    def run(self, *args, **kwargs):
        server = self.server
        if hasattr(server, "run"):
            server.run(*args, **kwargs)
        elif hasattr(server, "serve_forever"):
            server.serve_forever(*args, **kwargs)
        else:
            asyncio.run(self.serve(*args, **kwargs))

    def handle_exit(self, *args, **kwargs):
        server = self.server
        if hasattr(server, "handle_exit"):
            server.handle_exit(*args, **kwargs)
        elif hasattr(server, "shutdown"):
            server.shutdown()
        elif hasattr(server, "close"):
            server.close()
        else:
            raise TypeError("Cannot close server:", server)

    @classmethod
    def from_config(cls, **kwargs):
        return cls(**kwargs)


class Subsystems:

    def __init__(self, **systems:Dict[str, Server]):
        self.systems = systems

    def handle_exit(self, *args, **kwargs):
        for system in self.systems:
            system.handle_exit()

    async def serve(self):
        tasks = []
        self.install_signal_handlers()
        import uvicorn
        uvicorn.Server.install_signal_handlers = lambda *args, **kwargs: None

        for name, system in self.systems.items():
            #system._disable_signals()
            task = asyncio.create_task(system.serve())
            tasks.append(task)
        await asyncio.wait(tasks)

    def run(self):
        asyncio.run(self.serve())

    def __getitem__(self, name) -> Server:
        "Get name of the app"
        if isinstance(name, str):
            return self.systems[name]
        else:
            return Subsystems(**{name: s for name, s in self.systems.items() if name in name})

    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError:  # pragma: no cover
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)

    def handle_exit(self, *args, **kwargs):
        for sys in self.systems.values():
            sys.handle_exit(*args, **kwargs)
    
    @classmethod
    def from_config(self, d:dict):
        from subsystems.config import Config
        return Config.parse(d)