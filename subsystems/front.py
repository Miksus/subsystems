from pathlib import Path
from typing import Callable, List
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse

from subsystems.utils.modules import load_instance
from .servers import SignalServer

ROOT_APP = Path(__file__).parent / "app"
PATH_INDEX = ROOT_APP / "index.html"

def create_react_app(app:FastAPI, path:Path, index_name="index.html"):
    react_path = Path(path)
    app_content = (react_path / index_name).read_text()

    app.mount("/static", StaticFiles(directory=react_path / "static"), name="static")

    @app.get("/")
    async def get_root(request: Request):
        return HTMLResponse(app_content)

    @app.route("/{full_path:path}")
    async def get_page(request: Request, full_path: str=None):
        #return RedirectResponse(url="/index.html")
        return HTMLResponse(app_content)
    return app

def create_app(app=None, react_config:dict=None):

    if app is None:
        app = FastAPI()
    elif isinstance(app, str):
        app = load_instance(app, default="app")

    @app.get("/_configs")
    async def get_page(request: Request, full_path: str=None):
        return JSONResponse(app.extra)

    if react_config is not None:
        app = create_react_app(app, **react_config)
    else:
        app = create_react_app(app, path=ROOT_APP, index_name="index.html")
    
    return app

class Frontend:

    on_shutdown: Callable = None

    def __init__(self, app:FastAPI, backend:str=None, **kwargs):
        self.app = app
        self.config = kwargs
        self.backend = backend

    async def serve(self):
        self.server = self.create_server()
        await self.server.serve()

    def run(self):
        self.server = self.create_server()
        self.server.run()

    def create_server(self):
        server = SignalServer(
            uvicorn.Config(
                app=self.app,
                **self.config
            ),
            handle_exit=self.handle_exit
        )
        return server

    def handle_exit(self, server: SignalServer, sig:int, frame):
        if self.on_shutdown is not None:
            self.on_shutdown(server, sig, frame)

    def add_backend(self, url:str):
        "Add backend to the API endpoints"
        self.app.extra["backend"] = url

    def get_urls(self) -> List[str]:
        host = self.config['host']
        port = self.config['port']
        return [f"http://{host}:{port}", f"https://{host}:{port}"]
