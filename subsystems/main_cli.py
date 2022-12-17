import argparse
from .main import main as _main

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
        prs.add_argument('--scheduler', dest='app_sched', default=None, help="Import path to the scheduler")
        prs.add_argument('--api', dest='app_back', default=None, help="Import path to the API")
        prs.add_argument('--frontends', dest='urls_front', default=None, type=str, nargs='+', help="URLs for frontends")

    for prs in (front, full):
        prs.add_argument('--app', dest='app_front', default=None, help="Import path to the app")
        prs.add_argument('--backend', dest='url_back', default=None, help="URL for backend API")

    parser.set_defaults(
        host_back=host_back,
        port_back=port_back,
        host_front=host_front,
        port_front=port_front,
    )

    args = parser.parse_args(args)
    return args

def main(args=None):
    args = parse_args(args)
    _main(**vars(args))

if __name__ == "__main__":
    main()