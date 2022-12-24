from gunicorn.config import Config
from gunicorn.app.wsgiapp import WSGIApplication

class GunicornApplication(WSGIApplication):
    
    def __init__(self, app_uri, host, port, **kwargs):
        self._custom_conf = kwargs
        super().__init__()

        # Settiing custom settings
        self.app_uri = app_uri
        for key, value in kwargs.items():
            self.cfg.set(key, value)
    
    def load_config(self):
        # init configuration
        self.app_uri = None
        for key, value in self._custom_conf.items():
            self.cfg.set(key, value)