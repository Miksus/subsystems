from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from subsystems.utils.modules import load_instance
from rocketry import Rocketry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from subsystems.utils.modules import load_instance

from .api.router import create_router
from .scheduler import create_app as create_scheduler

PATH_REACT_APP = Path(__file__).parent / "app" / "index.html"

def create_api(app:FastAPI=None, scheduler:Rocketry=None, **kwargs):

    if app is None:
        app = FastAPI(
            title="Rocketry with FastAPI",
            description="This is a REST API for a scheduler. It uses FastAPI as the web framework and Rocketry for scheduling."
        )
    elif isinstance(app, str):
        app = load_instance(app, default="app")

    # Add routers
    # -----------

    app.include_router(create_router(scheduler), **kwargs)
    return app

def create_react_app(app:FastAPI, path:Path):
    react_path = path.parent
    app_content = path.read_text()

    app.mount("/static", StaticFiles(directory=react_path / "static"), name="static")

    @app.get("/")
    async def get_root(request: Request):
        return HTMLResponse(app_content)

    @app.route("/{full_path:path}")
    async def get_page(request: Request, full_path: str=None):
        #return RedirectResponse(url="/index.html")
        return HTMLResponse(app_content)
    return app

def create_app(app=None, react_build:Path=None):

    if app is None:
        app = FastAPI()
    elif isinstance(app, str):
        app = load_instance(app, default="app")

    @app.get("/_configs")
    async def get_page(request: Request, full_path: str=None):
        return JSONResponse(app.extra)

    if react_build is not None:
        app = create_react_app(app, path=Path(react_build))
    else:
        app = create_react_app(app, path=PATH_REACT_APP)
    
    return app