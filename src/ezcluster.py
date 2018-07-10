
import os
import argparse
#import logging
import logging.config
import yaml
import sys
from pykwalify.core import Core as kwalify

import misc
import config
from misc import ERROR
from dumper import Dumper
from module import buildModules, buildTargetFileByName
from schema import buildSchema
from generator import generate


logger = logging.getLogger("ezcluster.main")


def main():
    mydir =  os.path.dirname(os.path.realpath(__file__)) 
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True)
    parser.add_argument('--mark', choices=["none", "both", "start", "end"])
    parser.add_argument('--dump', action='store_true')
    
    param = parser.parse_args()

    sourceFile = param.src
    sourceFileDir = os.path.dirname(sourceFile)
    
    loggingConfFile =  os.path.join(mydir, "./logging.yml")
    logging.config.dictConfig(yaml.load(open(loggingConfFile)))

    logger.info("Will handle '{}'".format(sourceFile))

    cluster = yaml.load(open(sourceFile))
    targetFolder = misc.appendPath(sourceFileDir, cluster["build_folder"] if "build_folder" in cluster else "build")
    misc.ensureFolder(targetFolder)

    logger.info("Build folder: '{}'".format(targetFolder))
    
    modulesPath = [ misc.appendPath(mydir, "../modules"), misc.appendPath(sourceFileDir, "modules")]
    logger.debug("Module path:'{}'".format(modulesPath))
    modules = buildModules(cluster, modulesPath)

    infra = config.buildInfra(mydir, sourceFileDir)
    repositories = config.buildRepositories(sourceFileDir)

    schema = buildSchema(mydir, modules)

    if param.dump:
        dumper = Dumper(targetFolder)
        dumper.dump("schema.json", schema)

    k = kwalify(source_data = cluster, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(sourceFile, k.errors))
    
    data = {}
    data['sourceFileDir'] = sourceFileDir
    data['ezclusterHome'] = misc.appendPath(mydir,"..")
    data["rolePaths"] = set()
                
    model = {}
    model['cluster'] = cluster
    model['infra'] = infra
    model['repositories'] = repositories
    model['data'] = data
            
    for module in modules:
        module.groom(model)

    targetFileByName = buildTargetFileByName(modules)
        

    if param.dump:
        dumper.dump("cluster.json", model['cluster'])
        dumper.dump("data.json", model['data'])
        dumper.dump("infra.json", model['infra'])
        dumper.dump("repositories.json", model['repositories'])
        dumper.dump("targetFileByName.json", targetFileByName)
    
    generate(targetFileByName, targetFolder, model, param.mark)

if __name__ == '__main__':
    sys.exit(main())
    
    