"""
This file contains Rocketry app.
Add your tasks here, conditions etc. here.
"""
from typing import Union
import importlib
from redbird.repos import SQLRepo, MemoryRepo
from sqlalchemy import create_engine

from rocketry import Rocketry
from rocketry.args import TaskLogger, Config, EnvArg
from rocketry.log import MinimalRecord

from subsystems.utils.modules import load_instance

def setup_app(logger=TaskLogger(), config=Config(), env=EnvArg("ENV", default="dev")):
    "Set up the app"
    if env == "prod":
        conn_string = "sqlite:///app.db"
        repo = SQLRepo(engine=create_engine(conn_string), table="tasks", model=MinimalRecord, id_field="created", if_missing="create")

        config.silence_task_prerun = True
        config.silence_task_logging = True
        config.silence_cond_check = True
    else:
        repo = MemoryRepo(model=MinimalRecord, if_missing="create")

        config.silence_task_prerun = False
        config.silence_task_logging = False
        config.silence_cond_check = False
    
    logger.set_repo(repo)

def create_app(app:Union[Rocketry, str]=None):

    if app is None:
        app = Rocketry(config={"execution": "async"})

        app.setup(func=setup_app)

        from .tasks import example
        app.include_grouper(example.group)
    elif isinstance(app, str):
        # app is import path
        app = load_instance(app, default="app")
    return app
