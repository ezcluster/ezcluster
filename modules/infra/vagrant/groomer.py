

import logging
import os
from misc import ERROR
import ipaddress
import yaml


loggerConfig = logging.getLogger("ezcluster.config")

                
 
def findConfig(fileName, initial, location, cpt):
    x = os.path.join(location , fileName)
    if os.path.isfile(x):
        # Found !
        loggerConfig.info("Use '{0}' as config file".format(x))
        return x
        #return edict(yaml.load(open(x)))
    else:
        if location == "" or location == "/" :
            ERROR("Unable to locate a {0} file in '{1}' and upward".format(fileName, initial))
        else:
            if cpt < 20:
                return findConfig(fileName, initial, os.path.dirname(location), cpt + 1)
            else:
                raise Exception("Too many lookup")
                

def buildRepositories(sourceFileDir):
    repoFile = findConfig('infra/repositories.yml', sourceFileDir, sourceFileDir, 0)
    repos = yaml.load(open(repoFile))
    return repos

SYNCED_FOLDERS="synced_folders"

def groom(module, model):
    if 'infra/core' not in model["cluster"]["modules"]:
        ERROR("Module 'core' is mandatory before module 'vagrant'")
    if "local_yum_repo" not in model["cluster"]["vagrant"]:
        model["cluster"]["vagrant"]["local_yum_repo"] = True
    repositories = buildRepositories(model['data']['sourceFileDir'])
    model['repositories'] = repositories
    for node in model['cluster']['nodes']:
        if not SYNCED_FOLDERS in node:
            node[SYNCED_FOLDERS] = []
        role = model["data"]["roleByName"][node["role"]]
        if SYNCED_FOLDERS in role:
            node[SYNCED_FOLDERS] += role[SYNCED_FOLDERS]
        if SYNCED_FOLDERS in model["cluster"]["vagrant"]:
            node[SYNCED_FOLDERS] += model["cluster"]["vagrant"][SYNCED_FOLDERS]
    
    
    


def dump(module, model, dumper):
    dumper.dump("repositories.json", model['repositories'])
        