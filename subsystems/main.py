

from pathlib import Path

from subsystems.config import Config, get_template


ROOT = Path(__file__).parent

DEFAULT_CONF = "subsystems.yaml"

def init_subsystems(tmpl):
    content = get_template(tmpl)
    file = Path(DEFAULT_CONF)
    file.write_text(content)


def main(
    command:str,
    **kwargs
):
    if command == "launch":
        tmpl = kwargs.pop("template", None)
        if tmpl:
            subsystems = Config.parse_template(tmpl, scheduler=kwargs.pop("scheduler"))
        else:
            config = kwargs.pop("config")
            if config is None:
                config = DEFAULT_CONF
            subsystems = Config.parse_yaml(config, **kwargs)
        app = kwargs.pop("app", None)
        if app is None:
            subsystems.run()
        else:
            subsystems[app].run()
    elif command == "init":
        tmpl = kwargs.pop("template", "rocketry")
        init_subsystems(tmpl)