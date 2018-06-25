
import os
import argparse
#import logging
import logging.config
import yaml
import sys
from collections import namedtuple
from pykwalify.core import Core as kwalify


from misc import ERROR
import schema



logger = logging.getLogger("ezcluster.main")

Module = namedtuple('Module', ["name", "path"])



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
            modules.append(Module(m, lookupModule(m, modulesPath)))
                



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

    logger.info("Will handle {}".format(sourceFile))
    
    modulesPath = [ os.path.join(mydir, "../modules"), os.path.dirname(sourceFile)]
    logger.debug("Module path:'{}'".format(modulesPath))
    
    cluster = yaml.load(open(sourceFile))
    modules = buildModules(cluster, modulesPath)
    schema = schema.buildSchema(modules)
    


    k = kwalify(source_data = cluster, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(sourceFile, k.errors))
            
        
    

if __name__ == '__main__':
    sys.exit(main())
    
    