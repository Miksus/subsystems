import asyncio
import threading
import signal
from typing import Dict

from .servers import ServerBase
from subsystems.utils.modules import load_instance

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

class Subsystems:

    def __init__(self, **systems:Dict[str, ServerBase]):
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

    def __getitem__(self, name) -> ServerBase:
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