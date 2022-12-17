import pytest
from subsystems.main_cli import parse_args

@pytest.mark.parametrize("args,output",
    [
        pytest.param([], {'command': None, 'host_back': 'localhost', 'port_back': 8080, 'host_front': 'localhost', 'port_front': 3000}, id="defaults"),
        pytest.param(["project"], {
            'command':'project',
            'host_back':'localhost',
            'port_back':8080,
            'host_front':'localhost',
            'port_front':3000,
            'app_front':None,
            'url_back':None,
            'app_sched':None,
            'app_back':None,
            'origins':None,
        }, id="project (defaults)"),
        pytest.param(["back"], {
            'command': 'back', 
            'host_back': 'localhost', 'port_back': 8080, 
            'host_front': 'localhost', 'port_front': 3000, 
            'app_back': None, 'app_sched': None, 
            #'app_front': None, 
            'origins': None,
        }, id="back (defaults)"),
        pytest.param(["front"], {
            'command': 'front', 
            'host_back': 'localhost', 'port_back': 8080, 
            'host_front': 'localhost', 'port_front': 3000,
            'app_front': None,
            #'app_sched': None, 'app_back': None, 
            'url_back': None
        }, id="front (defaults)"),

        pytest.param(["back", "--host", "0.0.0.0", "--port", "8090", "--api", "myapi.myapp:app", "--scheduler", "mysched.myapp:app", "--origins", "http://example.com", "https://example.com"], {
            'command': 'back', 
            'host_back': '0.0.0.0', 'port_back': 8090, 
            'host_front': 'localhost', 'port_front': 3000, 
            'app_back': "myapi.myapp:app", 'app_sched': "mysched.myapp:app", 
            #'app_front': None, 
            'origins': ['http://example.com', 'https://example.com'],
        }, id="back"),
        pytest.param(["front", "--host", "0.0.0.0", "--port", "3100", "--app", "myfront.myapp:app", "--backend", "http://example.com"], {
            'command': 'front', 
            'host_back': 'localhost', 'port_back': 8080, 
            'host_front': '0.0.0.0', 'port_front': 3100, 
            #'app_back': None, 'app_sched': None, 
            'app_front': "myfront.myapp:app", 
            'url_back': "http://example.com", 
            #'urls_front': None,
        }, id="front"),
    ]
)
def test_parser(args, output):
    args = parse_args(args)
    assert vars(args) == output