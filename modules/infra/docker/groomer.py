

from misc import ERROR

def groom(module, model):
    if not "docker" in model["cluster"]:
        model["cluster"]["docker"] = {}
    if not "users" in model["cluster"]["docker"]:
        model["cluster"]["docker"]["users"] = []
