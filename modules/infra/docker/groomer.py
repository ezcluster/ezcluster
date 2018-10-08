

from misc import ERROR

def groom(module, model):
    """
    if not "docker" in model["cluster"]:
        model["cluster"]["docker"] = {}
    if not "users" in model["cluster"]["docker"]:
        model["cluster"]["docker"]["users"] = []
    if "version" in model["cluster"]["docker"]:
        version = model["cluster"]["docker"]["version"]
        model["data"]["dockerPackage"] = "docker-ce-" + version + ".ce"
        # Patch: https://github.com/moby/moby/issues/33930
        if version.startswith("17.03"):
            model["data"]["dockerSelinuxPackage"] = "docker-ce-selinux-" + version + ".ce"
    else: 
        model["data"]["dockerPackage"] = "docker-ce"
    """
    version = model["cluster"]["docker"]["version"]
    if not version in model["repositories"]['docker']:
        ERROR("Docker version '{}' is not defined in our repository".format(version))