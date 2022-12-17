import importlib

def load_instance(s:str, default):
    parts = s.split(":", 1)
    if len(parts) == 1:
        module_name = parts[0]
        instance_name = default
    else:
        module_name, instance_name = parts
    module = importlib.import_module(module_name)
    return getattr(module, instance_name)