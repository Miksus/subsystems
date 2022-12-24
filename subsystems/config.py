
import asyncio
import importlib
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, Extra
from jinja2 import Environment

from subsystems.utils.modules import load_instance
from .systems import Subsystems
from .servers import create_server, get_server_class, DummyServer

ROOT = Path(__file__).parent
PATH_APP = ROOT / "app"
ROOT_TEMPLATES = ROOT / "templates"

JINJA_ENV = Environment(
    variable_start_string="${{",
    variable_end_string="}}",
)

APP_ALIASES = {
    "FastAPI": 'fastapi.FastAPI',
    "Flask": 'flask.Flask',
    "Rocketry": 'rocketry.Rocketry',
}

SERVER_ALIASES = {
    "uvicorn": "uvicorn.Server",
    "waitress": "waitress.create_server",
    "werkzeug": "werkzeug.serving.make_server",
}

class ServerConfig(BaseModel):
    class Config:
        extra = Extra.allow
    
    type: str = Field(description="Type of the server to run the instance")
    use_path: Optional[bool] = None

    def create(self, app_instance=None, app_path=None):
        type = self.type
        if type in SERVER_ALIASES:
            type = SERVER_ALIASES[type]
        config = self.dict(exclude={"type", "use_path"})
        if "port" in config:
            config["port"] = int(config['port'])
        return create_server(app_instance=app_instance, app_path=app_path, cls_name=type, config=config)

    @property
    def use_path_only(self):
        if self.use_path is not None:
            return self.use_path
        
        type = self.type
        if type is not None:
            try:
                cls = get_server_class(type)
            except KeyError:
                pass
            else:
                return not cls.use_instance
        return False

class InstanceConfig(BaseModel):
    class Config:
        extra = Extra.allow
    
    type: Optional[str] = Field(description="Type of the instance/app")
    instance: Optional[str] = Field(description="Import path for the app instance")

    def create(self, **kwargs):
        "Create the instance"
        if self.instance is not None:
            return load_instance(self.instance)

        type = self.type
        if type in APP_ALIASES:
            type = APP_ALIASES[type]
        cls = load_instance(type)
        params = self.dict(exclude={"type", "instance", "lazy_load"})
        return self.initiate(cls, **params, **kwargs)

    def get_path(self):
        return self.instance

    def initiate(self, cls, **kwargs):
        if hasattr(cls, "from_config"):
            return cls.from_config(**kwargs)
        return cls(**kwargs)

class AppConfig(BaseModel):
    app: InstanceConfig = Field(description="Type of the instance/app")
    server: Optional[ServerConfig] = Field(description="Server to run the instance")

    def create(self):
        if self.server is None:
            instance = self.app.create()
            server = DummyServer(app_instance=instance)
        elif self.server.use_path_only:
            server = self.server.create(app_path=self.app.get_path())
        else:
            instance = self.app.create()
            server = self.server.create(app_instance=instance)
        return server

class Config(BaseModel):
    apps: Dict[str, AppConfig]

    @classmethod
    def parse(cls, conf:dict):
        c = cls(**conf)
        return c.create()

    @classmethod
    def parse_yaml(cls, __file, **kwargs):
        c = parse_file(__file, **kwargs)
        return cls.parse(c)

    @classmethod
    def parse_template(cls, __tmpl, **kwargs):
        return cls.parse_yaml(ROOT_TEMPLATES / f"{__tmpl}.yaml", **kwargs)

    def _create_apps(self):
        return {
            name: app_config.create()
            for name, app_config in self.apps.items()
        }

    def create(self):
        "Turn config to actual subsystems"
        return Subsystems(**self._create_apps())

def parse_file(__path, **kwargs):
    content = Path(__path).read_text()
    tmpl = JINJA_ENV.from_string(content)

    kwargs.update(
        __dir_subsystems__=str(ROOT)
    )

    yaml_content = tmpl.render(**kwargs)
    return yaml.safe_load(yaml_content)

def get_template(tmpl) -> str:
    return (ROOT_TEMPLATES / f"{tmpl}.yaml").read_text()