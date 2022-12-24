import pytest
from rocketry.conds import scheduler_cycles
from rocketry import Rocketry

from subsystems.apps import AutoAPI
#from subsystems.apps import create_api, create_scheduler
from fastapi.testclient import TestClient

def do_success():
    ...

@pytest.fixture()
def scheduler():
    app = Rocketry()
    app.params(myparam="hello")
    app.task(start_cond="every 10 seconds", func=do_success, name="do_short")
    app.task(start_cond="every 10 seconds", func=do_success, name="do_stuff")
    app.task(start_cond="every 10 seconds", func=do_success, name="do_things")
    return app

@pytest.fixture()
def api(scheduler):
    app = AutoAPI(scheduler=scheduler)
    return app

@pytest.fixture()
def client(api):
    return TestClient(api)

def test_get_tasks(client):
    response = client.get("/tasks")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 0

def test_get_config(client):
    response = client.get("/session/config")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, dict)
    assert set(body.keys()) >= {"task_priority", "task_priority", "multilaunch", "timeout", "shut_cond", "cycle_sleep"}

def test_get_params(client):
    response = client.get("/session/parameters")
    assert response.status_code == 200

    body = response.json()
    assert body == {"myparam": "hello"}

def test_post_task_run(client):
    resp = client.get("/tasks/do_short")
    assert resp.status_code == 200
    assert not resp.json()["set_running"]

    response = client.post("/tasks/do_short/run")
    assert response.status_code == 200

    assert client.get("/tasks/do_short").json()["set_running"]

def test_post_task_disable_enable(client):
    assert not client.get("/tasks/do_short").json()["disabled"]

    for _ in range(2):
        response = client.post("/tasks/do_short/disable")
        assert response.status_code == 200
        assert client.get("/tasks/do_short").json()["disabled"]

    for _ in range(2):
        response = client.post("/tasks/do_short/enable")
        assert response.status_code == 200
        assert not client.get("/tasks/do_short").json()["disabled"]

def test_get_logs(scheduler, client):
    scheduler.session.config.shut_cond = scheduler_cycles(1)
    scheduler.session.config.instant_shutdown = True
    scheduler.run()
    response = client.get("/logs")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) > 3