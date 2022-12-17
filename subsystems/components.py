from typing import Callable

import uvicorn
from fastapi import FastAPI

from subsystems.servers import SignalServer

class Layer:
    on_shutdown: Callable = None

    def __init__(self, app:FastAPI, **kwargs):
        self.app = app
        self.config = kwargs

    def create_server(self):
        server = SignalServer(
            uvicorn.Config(
                app=self.app,
                **self.config
            ),
            handle_exit=self.handle_exit
        )
        return server

    async def serve(self):
        self.server = self.create_server()
        await self.server.serve()

    def run(self):
        self.server = self.create_server()
        self.server.run()

    def handle_exit(self, server: SignalServer, sig:int, frame):
        if self.on_shutdown is not None:
            self.on_shutdown(server, sig, frame)