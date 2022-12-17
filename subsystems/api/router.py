from typing import List, Optional
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
import time

from fastapi import APIRouter, Query
from redbird.oper import between, in_, greater_equal
from rocketry import Rocketry

from subsystems.api.models import Log, TaskModel


# Session Config
# --------------

class RocketryRoutes:

    def __init__(self, app:Rocketry):
        self.app = app

    async def get_session_config(self):
        return self.session.config.dict(exclude={"time_func", "func_run_id", "cls_lock"})

    async def patch_session_config(self, values:dict):
        for key, val in values.items():
            setattr(self.session.config, key, val)

    # Session Parameters
    # ------------------

    async def get_session_parameters(self):
        return self.session.parameters

    async def get_session_parameters(self, name):
        return self.session.parameters[name]

    async def put_session_parameter(self, name:str, value):
        self.session.parameters[name] = value

    async def delete_session_parameter(self, name:str):
        del self.session.parameters[name]


    # Session Actions
    # ---------------

    async def shut_down_session(self):
        self.session.shut_down()


    # Task
    # ----

    async def get_tasks(self):
        return [
            TaskModel.from_task(task)
            for task in self.session.tasks
        ]

    async def get_task(self, task_name:str):
        return TaskModel.from_task(self.session[task_name])
        
    async def patch_task(self, task_name:str, values:dict):
        task = self.session[task_name]
        for attr, val in values.items():
            setattr(task, attr, val)


    # Task Actions
    # ------------

    async def disable_task(self, task_name:str):
        task = self.session[task_name]
        task.disabled = True

    async def enable_task(self, task_name:str):
        task = self.session[task_name]
        task.disabled = False

    async def terminate_task(self, task_name:str):
        task = self.session[task_name]
        task.force_termination = True

    async def run_task(self, task_name:str):
        task = self.session[task_name]
        task.run()


    # Logging
    # -------
    async def get_logs(self, action: Optional[List[Literal['run', 'success', 'fail', 'terminate', 'crash', 'inaction']]] = Query(default=[]),
                            min_created: Optional[int]=Query(default=None), max_created: Optional[int] = Query(default=None),
                            past: Optional[int]=Query(default=None),
                            limit: Optional[int]=Query(default=None),
                            task: Optional[List[str]] = Query(default=None)):
        filter = {}
        if action:
            filter['action'] = in_(action)
        if (min_created or max_created) and not past:
            filter['created'] = between(min_created, max_created, none_as_open=True)
        elif past:
            filter['created'] = greater_equal(time.time() - past)
        
        if task:
            filter['task_name'] = in_(task)

        repo = self.session.get_repo()
        logs = repo.filter_by(**filter).all()
        if limit:
            logs = logs[max(len(logs)-limit, 0):]
        logs = sorted(logs, key=lambda log: log.created, reverse=True)
        logs = [Log(**vars(log)) for log in logs]

        return logs

    async def get_task_logs(self, task_name:str,
                            action: Optional[List[Literal['run', 'success', 'fail', 'terminate', 'crash', 'inaction']]] = Query(default=[]),
                            min_created: Optional[int]=Query(default=None), max_created: Optional[int] = Query(default=None)):
        filter = {}
        if action:
            filter['action'] = in_(action)
        if min_created or max_created:
            filter['created'] = between(min_created, max_created, none_as_open=True)

        return self.session[task_name].logger.filter_by(**filter).all()

    @property
    def session(self):
        return self.app.session

def create_router(app:Rocketry, **kwargs):
    router = APIRouter(**kwargs)

    routes = RocketryRoutes(app)

    router.get("/session/config", tags=["config"])(routes.get_session_config)
    router.patch("/session/config", tags=["config"])(routes.patch_session_config)

    router.get("/session/parameters", tags=["parameters"])(routes.get_session_parameters)
    router.get("/session/parameters/{name}", tags=["parameters"])(routes.get_session_parameters)
    router.delete("/session/parameters/{name}", tags=["parameters"])(routes.delete_session_parameter)

    router.post("/session/shut_down", tags=["session"])(routes.shut_down_session)

    router.get("/tasks", response_model=List[TaskModel], tags=["task"])(routes.get_tasks)
    router.patch("/tasks/{task_name}", tags=["task"])(routes.patch_task)

    router.post("/tasks/{task_name}/disable", tags=["task"])(routes.disable_task)
    router.post("/tasks/{task_name}/enable", tags=["task"])(routes.enable_task)
    router.post("/tasks/{task_name}/terminate", tags=["task"])(routes.terminate_task)
    router.post("/tasks/{task_name}/enable", tags=["task"])(routes.run_task)

    router.get("/logs", tags=["logs"])(routes.get_logs)
    router.post("/task/{task_name}/logs", tags=["task", "logs"])(routes.get_task_logs)

    return router
