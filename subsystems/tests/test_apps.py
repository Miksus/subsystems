import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from subsystems.apps import StaticApp
import subsystems

APP_ROOT = Path(subsystems.__file__).parent / "app"

def test_static_app():
    app = StaticApp(path=APP_ROOT / "index.html", static_path=APP_ROOT)
    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200
    cont_index = resp.content

    resp = client.get("/index.html")
    assert resp.status_code == 200
    assert resp.content == cont_index
    
    # Should return index.html 
    resp = client.get("/custom-route")
    assert resp.status_code == 200
    assert resp.content == cont_index