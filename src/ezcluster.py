# Copyright (C) 2018 BROADSoftware
#
# This file is part of EzCluster
#
# EzCluster is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EzCluster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with EzCluster.  If not, see <http://www.gnu.org/licenses/lgpl-3.0.html>.

import os
import argparse
#import logging
import logging.config
import yaml
import sys
from pykwalify.core import Core as kwalify

import misc
from misc import ERROR,findUpward
from dumper import Dumper
from plugin import appendPlugins, buildTargetFileByName, Plugin
from schema import buildSchema, buildConfigSchema
from generator import generate
from vault import initVault, SAFE_CONFIG, _SAFE_CONFIG_FILE_

logger = logging.getLogger("ezcluster.main")

PLUGINS_PATH="plugins_paths"

def buildConfig(sourceFileDir, baseConfigFile):
    configFile = findUpward(baseConfigFile, sourceFileDir)
    logger.info("Using '{}' as configuration file".format(configFile))
    config =  yaml.load(open(configFile), Loader=yaml.SafeLoader)
    if PLUGINS_PATH not in config:
        ERROR("Missing '{}' in configuration file".format(PLUGINS_PATH))
    # Adjust plugin path relative to the config file
    baseDir = os.path.dirname(configFile)
    for index, path in enumerate(config[PLUGINS_PATH]):
        config[PLUGINS_PATH][index] = misc.appendPath(baseDir, path)
    return (config, configFile)
    

def main():
    global vaultFactory 
    
    mydir =  os.path.dirname(os.path.realpath(__file__)) 
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True)
    parser.add_argument('--mark', choices=["none", "both", "start", "end"])
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--dumpPasswords', action='store_true')
    parser.add_argument('--out')    # Generate a file to set some variable
    
    param = parser.parse_args()

    loggingConfFile =  os.path.join(mydir, "./logging.yml")
    logging.config.dictConfig(yaml.load(open(loggingConfFile), Loader=yaml.SafeLoader))

    sourceFile = os.path.normpath(os.path.abspath(param.src))
    if not os.path.isfile(sourceFile):
        ERROR("File '{}' does not exists".format(sourceFile))
    logger.info("Will handle '{}'".format(sourceFile))
    sourceFileDir = os.path.dirname(sourceFile)
    
    cluster = yaml.load(open(sourceFile), Loader=yaml.SafeLoader)
    targetFolder = misc.appendPath(sourceFileDir, cluster["build_folder"] if "build_folder" in cluster else "build")
    misc.ensureFolder(targetFolder)
    logger.info("Build folder: '{}'".format(targetFolder))

    if "config_file" in cluster:
        baseConfigFile = cluster["config_file"]
    else:
        baseConfigFile = "ezconfig.yml"
    config, configFile = buildConfig(sourceFileDir, baseConfigFile)
    
    plugins = []
    plugins.append(Plugin("core", misc.appendPath(mydir, "../plugins/core")))
    logger.debug("Plugins path:'{}'".format(config[PLUGINS_PATH]))
    appendPlugins(plugins, cluster, config[PLUGINS_PATH])
    
    schema = buildSchema(mydir, plugins)
    configSchema, safeConfigSchema = buildConfigSchema(mydir, config[PLUGINS_PATH])

    if param.dump:
        dumper = Dumper(targetFolder, param.dumpPasswords)
        dumper.dump("schema.json", schema)
        dumper.dump("config-schema.json", configSchema)
        dumper.dump("safe-config-schema.json", safeConfigSchema)
    else:
        dumper = None

    k = kwalify(source_data = cluster, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(sourceFile, k.errors))
    
    k = kwalify(source_data = config, schema_data=configSchema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Configuration problem {0}: {1}".format(configFile, k.errors))
    
    data = {}
    data['sourceFileDir'] = sourceFileDir
    data["targetFolder"] = targetFolder
    data['ezclusterHome'] = misc.appendPath(mydir,"..")
    data["rolePaths"] = set()
    data["configFile"] = configFile
                
    model = {}
    model['cluster'] = cluster
    model["config"] = config
    model['data'] = data

    initVault(model)
    
    if SAFE_CONFIG in model and safeConfigSchema != None:
        k = kwalify(source_data = model[SAFE_CONFIG], schema_data=safeConfigSchema)
        k.validate(raise_exception=False)
        if len(k.errors) != 0:
            ERROR("Configuration problem {0}: {1}".format(model["data"][_SAFE_CONFIG_FILE_], k.errors))
            
    for plugin in plugins:
        plugin.groom(model)

    for plugin in plugins:
        plugin.groom2(model)

    targetFileByName = buildTargetFileByName(plugins)

    if param.dump:
        dumper.dump("cluster.json", model['cluster'])
        dumper.dump("data.json", model['data'])
        dumper.dump("targetFileByName.json", targetFileByName)
        dumper.dump("config.json", config)
        if SAFE_CONFIG in model and dumper.unsafe:
            dumper.dump("safeConfig.json", model[SAFE_CONFIG]) 
        
        for plugin in plugins:
            plugin.dump(model, dumper)
    
    generate(targetFileByName, targetFolder, model, param.mark, dumper)
    
    if "out" in param:
        f = open(param.out, "w+")
        f.write("# Generated by ezcluster:\n")
        if "buildScript" in model["data"]:
            f.write('BUILD_SCRIPT="{}"\n'.format(model["data"]["buildScript"]))
        f.close()
    
if __name__ == '__main__':
    sys.exit(main())
    
    