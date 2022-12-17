import logging
from pathlib import Path
from textwrap import dedent

from .systems import Subsystems

ROOT = Path(__file__).parent
PATH_APP = ROOT / "app"

LOGGER = logging.getLogger(__name__)

def main(
    command,
    app_front=None, app_back=None, app_sched=None,
    host_front=None, port_front=None,
    host_back=None, port_back=None,
    url_back=None, urls_front=None
):
    hdlr = logging.StreamHandler()
    hdlr.setLevel(logging.INFO)
    LOGGER.addHandler(hdlr)
    LOGGER.setLevel(logging.INFO)

    systems = Subsystems(
        front=app_front,
        api=app_back,
        scheduler=app_sched,
        front_config={
            "host": host_front,
            "port": port_front,
            "workers": 1,
            "loop": "asyncio",
        },
        back_config={
            "host": host_back,
            "port": port_back,
            "workers": 1,
            "loop": "asyncio",
        }
    )
    systems.link(url_back=url_back, urls_front=urls_front)

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

            App: {systems.back.api.title}
            Host back: {systems.back.config['host']}
            Port back: {systems.back.config['port']}
            Frontends: {systems.back.frontends}
            
            """[1:]))
        systems.run()
