import logging
from pathlib import Path
from textwrap import dedent
from subsystems.back import Backend

from subsystems.front import Frontend

from .apps import create_app, create_api, create_scheduler
from .systems import Subsystems

ROOT = Path(__file__).parent
PATH_APP = ROOT / "app"

LOGGER = logging.getLogger(__name__)

def main(
    command,
    app_front=None, app_back=None, app_sched=None,
    host_front=None, port_front=None,
    host_back=None, port_back=None,
    url_back=None, origins=None,

    react_build=None,
):
    hdlr = logging.StreamHandler()
    hdlr.setLevel(logging.INFO)
    LOGGER.addHandler(hdlr)
    LOGGER.setLevel(logging.INFO)

    scheduler = create_scheduler(app_sched)

    systems = Subsystems(
        front=Frontend(
            app=create_app(app_front, react_build=react_build),
            host=host_front,
            port=port_front,
            workers=1,
            loop="asyncio",
        ),
        back=Backend(
            app=create_api(app_back, scheduler=scheduler),
            scheduler=scheduler,
            host=host_back,
            port=port_back,
            workers=1,
            loop="asyncio",
        ),
    )

    systems.link(url_back=url_back, origins=origins)

    if command == "front":
        front = systems.front
        LOGGER.info(dedent(f"""
            Running Front...
            App: {front.app.title}
            Host: {front.config['host']}
            Port: {front.config['port']}
            Backend: {front.backend}
            """[1:]))
        systems.front.run()
    elif command == "back":
        systems.back.run()
    else:
        LOGGER.info(dedent(f"""
            Running Front and back...
            App: {systems.front.app.title}
            Host front: {systems.front.config['host']}
            Port front: {systems.front.config['port']}
            Backend: {systems.front.backend}

            App: {systems.back.app.title}
            Host back: {systems.back.config['host']}
            Port back: {systems.back.config['port']}
            Frontends: {systems.back.frontends}
            
            """[1:]))
        systems.run()
