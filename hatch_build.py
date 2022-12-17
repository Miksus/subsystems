import shutil
import subprocess
import os
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

from hatch_jupyter_builder import npm_builder

def build_app(target_name, *args, **kwargs):
    npm_builder(target_name=target_name, *args, **kwargs, source_dir="/app")

def build_react():
    os.chdir("frontend")
    subprocess.call(["npm.cmd", "run",  "build"])
    os.chdir("..")

class CustomHook(BuildHookInterface):

    def initialize(self, *args, **kwargs):
        print("CUSTOM HOOK!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(os.getcwd())
        shutil.rmtree("subsystems/app", ignore_errors=True)
        shutil.copytree("app/build", "subsystems/app")
        #npm_builder(*args, **kwargs, source_dir="/app")
        #build_react()
        if self.target_name == 'wheel':
            ...
        elif self.target_name == 'sdist':
            ...