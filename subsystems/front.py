from pathlib import Path
from typing import List
from .components import Layer

class Frontend(Layer):

    def add_backend(self, url:str):
        "Add backend to the API endpoints"
        self.app.extra["backend"] = url

    def get_urls(self) -> List[str]:
        host = self.config['host']
        port = self.config['port']
        return [f"http://{host}:{port}", f"https://{host}:{port}"]

    @property
    def backend(self):
        return self.app.extra["backend"]