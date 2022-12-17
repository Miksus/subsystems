import logging
import argparse
from pathlib import Path
from textwrap import dedent


from .servers import ServerCluster
from .systems import Subsystems

ROOT = Path(__file__).parent
PATH_APP = ROOT / "app"

LOGGER = logging.getLogger(__name__)


def parse_args(args=None):
    # Defaults
    host_back = "localhost"
    port_back = 8080

    host_front = "localhost"
    port_front = 3000

    parser = argparse.ArgumentParser(description='Run API and scheduler.')

    subparsers = parser.add_subparsers(dest='command')

    # Run frontend
    front = subparsers.add_parser('front', help='Launch front-end app')
    front.add_argument('--host', dest='host_front', default=host_front, help="Host of the front-end app")
    front.add_argument('--port', dest='port_front', type=int, default=port_front, help="Port of the front-end app")

    # Run backend
    back = subparsers.add_parser('back', help='Launch back-end api and scheduler')
    back.add_argument('--api', dest='app_back', default=None, help="Import path to the API")
    back.add_argument('--scheduler', dest='app_sched', default=None, help="Import path to the scheduler")
    back.add_argument('--host', dest='host_back', default=host_back, help="Host of the back-end api")
    back.add_argument('--port', dest='port_back', type=int, default=port_back, help="Port of the back-end app")

    # Run both
    full = subparsers.add_parser('project', help='Launch front, back and the scheduler')
    
    full.add_argument('--host-back', dest='host_back', default=host_back, help="Host of the back-end api")
    full.add_argument('--port-back', dest='port_back', type=int, default=port_back, help="Port of the back-end app")
    full.add_argument('--host-front', dest='host_front', default=host_front, help="Host of the back-end api")
    full.add_argument('--port-front', dest='port_front', type=int, default=port_front, help="Port of the back-end app")

    # Add arguments shared by all and back-end
    for prs in (back, full):
        prs.add_argument('--app', dest='app_front', default=None, help="Import path to the app")
        prs.add_argument('--backend', dest='url_back', default=None, help="URL for backend API")

    for prs in (front, full):
        prs.add_argument('--scheduler', dest='app_sched', default=None, help="Import path to the scheduler")
        prs.add_argument('--api', dest='app_back', default=None, help="Import path to the API")
        prs.add_argument('--frontends', dest='urls_fronts', default=None, type=str, nargs='+', help="URLs for frontends")

    parser.set_defaults(
        host_back=host_back,
        port_back=port_back,
        host_front=host_front,
        port_front=port_front,
    )

    args = parser.parse_args(args)
    return args

def cli(args=None):
    hdlr = logging.StreamHandler()
    hdlr.setLevel(logging.INFO)
    LOGGER.addHandler(hdlr)
    LOGGER.setLevel(logging.INFO)

    args = parse_args(args)

    for attr in ("app_front", "app_back", "app_sched", "host_back", "port_back", "url_back", "urls_front"):
        if not hasattr(args, attr):
            setattr(args, attr, None)

    systems = Subsystems(
        front=args.app_front,
        api=args.app_back,
        scheduler=args.app_sched,
        front_config={
            "host": args.host_front,
            "port": args.port_front,
            "workers": 1,
            "loop": "asyncio",
        },
        back_config={
            "host": args.host_back,
            "port": args.port_back,
            "workers": 1,
            "loop": "asyncio",
        }
    )
    systems.link(url_back=args.url_back, urls_front=args.urls_front)

    if args.command == "front":
        front = systems.front
        LOGGER.info(dedent(f"""
            Running Front...
            App: {front.app.title}
            Host: {front.config['host']}
            Port: {front.config['port']}
            Backend: {front.backend}
            """[1:]))
        systems.front.run()
    if args.command == "back":
        systems.back.run()
    if args.command == "full":
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

if __name__ == "__main__":
    cli()