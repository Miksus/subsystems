import asyncio
from typing import Callable, Optional
from fastapi import FastAPI
from rocketry import Rocketry
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .components import Layer

from .servers import ServerCluster, SignalServer

class Backend(Layer):

    def __init__(self, app:FastAPI, scheduler:Optional[Rocketry]=None, **kwargs):
        self.app = app
        self.scheduler = scheduler
        self.config = kwargs

    async def serve(self):
        self.server = self.create_server()
        if self.scheduler is not None:
            cluster = ServerCluster(
                self.server, self.scheduler
            )
            await cluster.serve()
        else:
            await self.server.serve()

    def run(self):
        asyncio.run(self.serve())

    def handle_exit(self, server, sig:int, frame):
        self.scheduler.session.shut_down(force=server.force_exit)
        super().handle_exit(server, sig, frame)

    def add_frontends(self, origins=None):
        "Add frontend to CORS"
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def get_url(self):
        "Get URL to the backend"
        config = self.config
        host = config['host']
        port = config['port']
        return f'http://{host}:{port}'

    @property
    def frontends(self):
        for mw in self.app.user_middleware:
            if isinstance(mw, CORSMiddleware):
                return mw.allow_origins