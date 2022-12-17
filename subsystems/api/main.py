"""
This file contains FastAPI app.
Modify the routes as you wish.
"""

from rocketry import Rocketry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from subsystems.utils.modules import load_instance

from .router import create_router
def create_app(app:FastAPI=None, scheduler:Rocketry=None, **kwargs):

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