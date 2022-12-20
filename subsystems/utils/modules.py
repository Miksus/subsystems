import importlib

def load_instance(s:str):
    parts = s.split(":", 1)
    if len(parts) == 1:
        # Assumes the last dot is the instance ie. "fastapi.FastAPI"
        parts = s.rsplit(".", 1)
    mdl_name, cls_name = parts


    mld = importlib.import_module(mdl_name)
    inst = getattr(mld, cls_name)
    return inst