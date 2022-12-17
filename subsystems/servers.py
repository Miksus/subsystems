"""
This file combines the two applications.
"""

import asyncio
import uvicorn

class SignalServer(uvicorn.Server):
    """Customized uvicorn.Server
    
    Uvicorn server overrides signals and we need to include
    Rocketry to the signals."""
    def __init__(self, *args, handle_exit, **kwargs):
        super().__init__(*args, **kwargs)
        self.hook_handle_exit = handle_exit

    def handle_exit(self, sig: int, frame) -> None:
        self.hook_handle_exit(self, sig, frame)
        return super().handle_exit(sig, frame)

    def _handle_exit(self, sig: int, frame):
        super().handle_exit(sig, frame)

class ServerCluster:

    def __init__(self, *subservers):
        self.subservers = subservers

    async def serve(self):
        tasks = []
        for server in self.subservers:
            task = asyncio.create_task(server.serve())
            tasks.append(task)
        await asyncio.wait(tasks)

    def run(self):
        asyncio.run(self.serve())