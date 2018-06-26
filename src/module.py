

import os
import yaml

from misc import ERROR

class Module:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def getSchema(self):
        f = os.path.join(self.path, "_schema.yml")
        if os.path.exists(f):
            return yaml.load(open(f))
        else:
            return {}



def lookupModule(module, modulesPath):
    for path in modulesPath:
        p = os.path.join(path, module)
        if os.path.exists(p):
            return Module(module, p)
    ERROR("Unable to find module '{}'".format(module))
    

def buildModules(cluster, modulesPath):
    modules = []
    if "modules" in cluster:
        for m in cluster['modules']:
            modules.append(lookupModule(m, modulesPath))
    return modules
                

