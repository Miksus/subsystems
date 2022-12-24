from typing import Union
from dataclasses import dataclass
from shlex import shlex
from pathlib import Path
import shutil
import subprocess
import os
import logging
from typing import List
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

def run_cmd(cmd, **kwargs):
    kwargs.setdefault("shell", os.name == "nt")
    subprocess.check_call(cmd, **kwargs)

def get_program(prog:str) -> str:
    if not Path(prog).is_absolute():
        # If a command is not an absolute path find it first.
        path = shutil.which(prog)
        if not path:
            raise ValueError(f"Cannot find program: {prog}")
        return path
    return prog

def build_npm(path=".", npm=None, build_script="build"):
    path = Path(path).resolve()

    # Find a suitable default for the npm command.
    if npm is None:
        use_yarn = (path / "yarn.lock").exists()
        if use_yarn and not shutil.which("yarn"):
            use_yarn = False

        if use_yarn:
            npm = "yarn"
        else:
            npm = "npm"

    prog = get_program(npm)

    cmd_install = [prog, "install"]
    cmd_build = [prog, "run", build_script]

    LOGGER.info(f"Installing dependencies: {cmd_install}")
    run_cmd(cmd_install, cwd=path)
    LOGGER.info(f"Building with: {cmd_build}")
    run_cmd(cmd_build, cwd=path)

def copy_build(source, target):
    LOGGER.info(f"Copying {source} to {target}")
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(source, target)

def target_exists(dir):
    path = Path(dir)
    try:
        return any(Path(path).iterdir())
    except FileNotFoundError:
        return False


@dataclass
class BuildConfig:
    source: str = "."
    target: str = None
    build: str = "build"
    skip_exist: bool = False

    index: str = None # Placeholder for build skipped tests


class CustomHook(BuildHookInterface):

    def initialize(self, version, build_data):
        config = BuildConfig(**self.config)

        source_dir = Path(config.source).resolve()
        build_dir = source_dir / config.build
        target_dir = Path(config.target).resolve()

        LOGGER.info(f"Running hook with {config}")
        if os.getenv("SKIP_HATCH_NPM_BUILDER"):
            LOGGER.info("Builder ignored. Skipping.")
            if config.index is not None:
                placeholder = target_dir / config.index
                LOGGER.info(f"Creating placeholder index file: {placeholder}")
                target_dir.mkdir(exist_ok=True)
                placeholder.write_text("")
            return
        if target_exists(target_dir) and config.skip_exist:
            LOGGER.info("Target exists. Skipping.")
            return

        build_npm(path=source_dir)

        if target_dir is not None:
            copy_build(build_dir, target_dir)

        LOGGER.info(f"Build done")
