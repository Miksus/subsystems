import argparse
import json
from .main import main as _main

def parse_args(args=None):
    # Defaults
    host_back = "localhost"
    port_back = 8080

    host_front = "localhost"
    port_front = 3000

    parser = argparse.ArgumentParser(description='Subsystem CLI')

    subparsers = parser.add_subparsers(dest='command')

    init = subparsers.add_parser('init', help='Create subsystem config file')
    init.add_argument('template', default="rocketry")

    # Run backend
    launch = subparsers.add_parser('launch', help='Launch an application')
    launch.add_argument('app', type=str, nargs='*', help="Applications to start")
    launch.add_argument('--config', default=None, help="Subsystem file")
    launch.add_argument('--template', default=None, help="Premade subsystem to use")

    # Run both
    full = subparsers.add_parser('project', help='Launch front, back and the scheduler')
    
    full.add_argument('--host-back', dest='host_back', default=host_back, help="Host of the back-end api")
    full.add_argument('--port-back', dest='port_back', type=int, default=port_back, help="Port of the back-end app")
    full.add_argument('--host-front', dest='host_front', default=host_front, help="Host of the back-end api")
    full.add_argument('--port-front', dest='port_front', type=int, default=port_front, help="Port of the back-end app")

    parsed, unknown = parser.parse_known_args(args)
    # Add unknown arguments to launch
    for arg in unknown:
        if arg.startswith(("-", "--")):
            launch.add_argument(arg.split('=')[0], type=str)

    args = parser.parse_args(args)
    return args

def main(args=None):
    args = parse_args(args)
    _main(**vars(args))

if __name__ == "__main__":
    main()