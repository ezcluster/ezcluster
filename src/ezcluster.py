
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
from module import buildModules
from schema import buildSchema

logger = logging.getLogger("ezcluster.main")


def main():
    mydir =  os.path.dirname(os.path.realpath(__file__)) 
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True)
    parser.add_argument('--mark', choices=["none", "both", "start", "end"])
    parser.add_argument('--dump', action='store_true')
    
    
    param = parser.parse_args()
    sourceFile = param.src
    
    loggingConfFile =  os.path.join(mydir, "./logging.yml")
    logging.config.dictConfig(yaml.load(open(loggingConfFile)))

    logger.info("Will handle '{}'".format(sourceFile))

    cluster = yaml.load(open(sourceFile))
    targetFolder = cluster["build_folder"] if "build_folder" in cluster else "build"
    targetFolder = os.path.join(os.path.dirname(sourceFile), targetFolder)
    misc.ensureFolder(targetFolder)

    logger.info("Build folder: '{}'".format(targetFolder))
    
    modulesPath = [ os.path.join(mydir, "../modules"), os.path.join(os.path.dirname(sourceFile), "modules")]
    logger.debug("Module path:'{}'".format(modulesPath))
    modules = buildModules(cluster, modulesPath)

    infra = config.buildInfra(os.path.dirname(sourceFile))
    repositories = config.buildRepositories(os.path.dirname(sourceFile))

    schema = buildSchema(modules)

    if param.dump:
        dumper = Dumper(targetFolder)
        dumper.dump("schema.json", schema)
        dumper.dump("cluster.json", cluster)
        dumper.dump("infra.json", infra)
        dumper.dump("repositories.json", repositories)
    

    k = kwalify(source_data = cluster, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(sourceFile, k.errors))
            


if __name__ == '__main__':
    sys.exit(main())
    
    