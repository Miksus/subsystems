
from .servers import ServerCluster

class Subsystems:

    def __init__(self, front, back):
        self.front = front
        self.back = back

    def link(self, url_back:str=None, origins=None):
        "Set front-end to back-end's CORS origins and back-end as the API to front-end"
        if url_back is None:
            url_back = self.back.get_url()
        if origins is None:
            origins = self.front.get_urls()

        self.front.add_backend(url_back)
        self.back.add_frontends(origins)

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