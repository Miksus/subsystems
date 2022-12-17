import asyncio
from typing import Callable, List
from fastapi import FastAPI
from platformdirs import api
from rocketry import Rocketry
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .servers import ServerCluster, SignalServer
from .api import create_app as create_api

class Backend:

    # Callbacks
    on_shutdown: Callable = None

    def __init__(self, api:FastAPI, scheduler:Rocketry, **kwargs):
        self.api = api
        self.scheduler = scheduler
        self.config = kwargs

    def create_server(self):
        server = SignalServer(
            uvicorn.Config(
                app=self.api,
                **self.config
            ),
            handle_exit=self.handle_exit
        )
        return server

    async def serve(self):
        self.server = self.create_server()
        cluster = ServerCluster(
            self.server, self.scheduler
        )
        #await self.server.serve()
        await cluster.serve()

    def run(self):
        asyncio.run(self.serve())

    def handle_exit(self, server, sig:int, frame):
        self.scheduler.session.shut_down(force=server.force_exit)
        if self.on_shutdown is not None:
            self.on_shutdown(server, sig, frame)


    def add_frontends(self, origins=None):
        "Add frontend to CORS"
        self.api.add_middleware(
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