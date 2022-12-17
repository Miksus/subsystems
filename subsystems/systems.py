
from .api import create_app as create_back_app
from .scheduler import create_app as create_scheduler

import uvicorn
from .front import Frontend, create_app as create_front_app
from .back import Backend, create_api
from .servers import SignalServer as BackendServer, ServerCluster


class Subsystems:

    def __init__(self, front, api, scheduler, front_config=None, back_config=None):
        scheduler = create_scheduler(scheduler)

        self.front = Frontend(
            app=create_front_app(front),
            **front_config,
        )
        self.back = Backend(
            api=create_api(api, scheduler=scheduler),
            scheduler=scheduler,
            **back_config,
        )

        self.front.backend = self.back.get_url()
        self.back.frontends = self.front.get_urls()

    def link(self, url_back:str=None, urls_front=None):
        "Set front-end to back-end's CORS origins and back-end as the API to front-end"
        if url_back is None:
            url_back = self.back.get_url()
        if urls_front is None:
            urls_front = self.front.get_urls()

        self.front.add_backend(url_back)
        self.back.add_frontends(urls_front)

        self.front.on_shutdown = self.handle_exit
        self.back.on_shutdown = self.handle_exit

    def handle_exit(self, server, *args, **kwargs):
        #if server is not self.front.server:
        print("Exit front")
        self.front.server._handle_exit(*args, **kwargs)
        #if server is not self.back.server:
        print("Exit back")
        self.back.server._handle_exit(*args, **kwargs)
        self.back.scheduler.session.shut_down()

        print(self.front.server.should_exit)
        print(self.back.server.should_exit)
        print(self.back.scheduler.session.scheduler._flag_shutdown.is_set())

    async def serve(self):
        "Serve all"
        cluster = ServerCluster(self.front, self.back)
        await cluster.serve()

    def run(self):
        "Run all"
        cluster = ServerCluster(self.front, self.back)
        cluster.run()