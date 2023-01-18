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
# import logging
import logging.config
import yaml
import sys
from pykwalify.core import Core as Kwalify

import misc
from misc import ERROR, findUpward
from dumper import Dumper
from plugin import appendPlugins, buildTargetFileByName, Plugin
from schema import buildSchema, buildConfigSchema
from generator import generate
from vault import initVault, SAFE_CONFIG, _SAFE_CONFIG_FILE_
from injectenv import injectenv, MissingVariableError

logger = logging.getLogger("ezcluster.main")

PLUGINS_PATH = "plugins_paths"

USER_PROFILE = "user_profile"


def buildConfig(sourceFileDir, baseConfigFile):
    configFile = findUpward(baseConfigFile, sourceFileDir)
    logger.info("Using '{}' as configuration file".format(configFile))
    with open(configFile, 'r') as file:
        data = file.read()
    try:
        data = injectenv(data)
    except MissingVariableError as err:
        ERROR("Error in file '{}': {}".format(configFile, err))
    config = yaml.safe_load(data)
    # config = yaml.load(open(configFile), Loader=yaml.SafeLoader)
    baseDir = os.path.dirname(configFile)
    if USER_PROFILE in config:
        userFile = misc.appendUserPath(baseDir, config[USER_PROFILE])
        del(config[USER_PROFILE])
        if not os.path.isfile(userFile):
            ERROR("User profile file '{}' does not exists".format(userFile))
        logger.info("Merging '{}' in configuration file".format(userFile))
        user_data = yaml.load(open(userFile), Loader=yaml.SafeLoader)
        config = misc.data_merge(config, user_data)
    if PLUGINS_PATH not in config:
        ERROR("Missing '{}' in configuration file".format(PLUGINS_PATH))
    # Adjust plugin path relative to the config file
    for index, path in enumerate(config[PLUGINS_PATH]):
        config[PLUGINS_PATH][index] = misc.appendPath(baseDir, path)
    return config, configFile
    

def main():
    global vaultFactory 
    
    mydir = os.path.dirname(os.path.realpath(__file__))
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', required=True)
    parser.add_argument('--mark', choices=["none", "both", "start", "end"])
    parser.add_argument('--dump', action='store_true')
    parser.add_argument('--dumpPasswords', action='store_true')
    parser.add_argument('--out')    # Generate a file to set some variable
    
    param = parser.parse_args()

    loggingConfFile = os.path.join(mydir, "./logging.yml")
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
    
    plugins = [Plugin("core", misc.appendPath(mydir, "../plugins/core"))]
    logger.debug("Plugins path:'{}'".format(config[PLUGINS_PATH]))
    appendPlugins(plugins, cluster, config[PLUGINS_PATH])
    
    schema = buildSchema(mydir, plugins)
    configSchema, safeConfigSchema = buildConfigSchema(mydir, config[PLUGINS_PATH])

    if param.dump:
        dumper = Dumper(targetFolder, param.dumpPasswords)
        dumper.dump("schema.dmp", schema)
        dumper.dump("config-schema.dmp", configSchema)
        dumper.dump("safe-config-schema.dmp", safeConfigSchema)
    else:
        dumper = None

    k = Kwalify(source_data=cluster, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(sourceFile, k.errors))
    
    k = Kwalify(source_data=config, schema_data=configSchema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Configuration problem {0}: {1}".format(configFile, k.errors))
    
    data = {
        'sourceFileDir': sourceFileDir,
        "targetFolder": targetFolder,
        'ezclusterHome': misc.appendPath(mydir, ".."),
        "rolePaths": set(),
        "configFile": configFile
    }

    model = {
        'cluster': cluster,
        "config": config,
        'data': data
    }

    initVault(model)
    
    if SAFE_CONFIG in model and safeConfigSchema is not None:
        k = Kwalify(source_data=model[SAFE_CONFIG], schema_data=safeConfigSchema)
        k.validate(raise_exception=False)
        if len(k.errors) != 0:
            ERROR("Configuration problem {0}: {1}".format(model["data"][_SAFE_CONFIG_FILE_], k.errors))
            
    for plugin in plugins:
        plugin.groom(model)

    for plugin in plugins:
        plugin.groom2(model)

    targetFileByName = buildTargetFileByName(plugins)

    if param.dump:
        dumper.dump("cluster.dmp", model['cluster'])
        dumper.dump("data.dmp", model['data'])
        dumper.dump("targetFileByName.dmp", targetFileByName)
        dumper.dump("config.dmp", config)
        if SAFE_CONFIG in model and dumper.unsafe:
            dumper.dump("safeConfig.dmp", model[SAFE_CONFIG]) 
        
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
    
    