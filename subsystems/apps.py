import asyncio
from typing import TYPE_CHECKING, Dict, Optional, Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from rocketry import Rocketry

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
        if self.static_path is not None:
            self.mount(self.static_route, StaticFiles(directory=self.static_path), name="static")
        
        @self.get("/")
        async def get_root(request: Request):
            return HTMLResponse(self.content)

        @self.get("/{full_path:path}")
        async def get_page(request: Request, full_path: str=None):
            #return RedirectResponse(url="/index.html")
            if full_path in self.custom_routes:
                content = self.custom_routes[full_path]
                return HTMLResponse(content) if isinstance(content, str) else JSONResponse(content)
            return HTMLResponse(self.content)
        


class RocketryAPI(FastAPI):

    def __init__(self, *args, scheduler:Rocketry, route_config:Optional[dict]=None, origins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(scheduler, str):
            scheduler = load_instance(scheduler)
        self._set_prebuilt_routes(scheduler, route_config)
        self._set_custom_middleware(origins=origins)

    def _set_prebuilt_routes(self, scheduler, config):
        if config is None:
            config = {}
        self.include_router(create_rocketry_routes(scheduler), **config)

    def _set_custom_middleware(self, origins):
        print(origins)
        if origins is not None:
            self.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

class ClusterApp:
    
    def __init__(self, apps:Dict[str, 'Server']):
        self.apps = apps

    async def serve(self, *args, **kwargs):
        tasks = []
        for name, app in self.apps.items():
            task = asyncio.create_task(app.serve(*args, **kwargs))
            tasks.append(task)
        await asyncio.wait(tasks)
    
    def run(self):
        asyncio.run(self.serve())

    @classmethod
    def from_config(cls, **kwargs):
        from .config import AppConfig
        apps = {}
        for name, conf in kwargs.items():
            app = AppConfig(**conf).create()
            apps[name] = app
        return cls(apps)

    def handle_exit(self, *args, **kwargs):
        print(self.apps)
        for system in self.apps.values():
            serv = system.server
            if hasattr(serv, "handle_exit"):
                serv.handle_exit(*args, **kwargs)
            else:
                serv.session.shut_down(force=True)
