import asyncio
from typing import TYPE_CHECKING, Dict, Optional, Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from rocketry import Rocketry
from subsystems.config import InstanceConfig

from subsystems.utils.modules import load_instance
from subsystems.utils.server import _disable_signals
from .api.router import create_rocketry_routes

if TYPE_CHECKING:
    from subsystems.systems import Server

class StaticApp(FastAPI):

    def __init__(self, *args, path:Union[str, Path], static_path:Union[str, Path]=None, static_route:str="/static", custom_routes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_path = static_path
        self.content = Path(path).read_text()
        self.static_route = static_route
        self.custom_routes = custom_routes if custom_routes is not None else {}

        self._set_prebuilt_routes()

    def _set_prebuilt_routes(self):
        static = StaticFiles(directory=self.static_path)
        
        @self.get("/")
        async def get_root(request: Request):
            return HTMLResponse(self.content)

        @self.get("/{full_path:path}")
        async def get_page(request: Request, full_path: str=None):
            #return RedirectResponse(url="/index.html")
            if full_path in self.custom_routes:
                content = self.custom_routes[full_path]
                return HTMLResponse(content) if isinstance(content, str) else JSONResponse(content)
            try:
                static_resp = await static.get_response(full_path, request.scope)
            except HTTPException as exc:
                if exc.status_code == 404:
                    # We return the app and hope the path is found there
                    return HTMLResponse(self.content)
                raise
            else:
                return static_resp


class AutoAPI(FastAPI):
    arg_server = '__server__'

    def __init__(self, scheduler:Rocketry, origins=None, route_config=None, **kwargs):

        super().__init__(scheduler=scheduler, **kwargs)
        self._set_events(scheduler)
        self._set_prebuilt_routes(scheduler, route_config)

        if origins:
            self.add_origins(origins)

    def _set_prebuilt_routes(self, scheduler, config):
        if config is None:
            config = {}
        self.include_router(create_rocketry_routes(scheduler), **config)

    def _set_events(self, scheduler):
        @self.on_event("startup")
        async def start():
            asyncio.create_task(scheduler.serve())

        @self.on_event("shutdown")
        async def shutdown():
            scheduler.session.shut_down()

    def add_server(self, serv):
        self.extra["scheduler"].params(**{self.arg_server: serv})

    def add_origins(self, origins):
        if origins is not None:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    @classmethod
    def from_config(cls, **kwargs):
        sched = kwargs.get('scheduler')
        if sched is not None:
            kwargs['scheduler'] = InstanceConfig(**sched).create()
        return cls(**kwargs)
