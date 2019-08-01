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
import errno
import socket

def ERROR(err):
    print "* * * * ERROR: {}".format(err)
    #raise Exception("xx")
    exit(1)

errors = []

def ADD_ERROR(err):
    global errors
    errors.append(err)
    
def FLUSH_ERROR():
    global errors
    if len(errors) > 0:
        for err in errors:
            print "* * * * ERROR: {}".format(err)
        exit(1)


def appendPath(p1, p2):
    if os.path.isabs(p2):
        return p2
    else:
        return os.path.normpath(os.path.join(p1, p2))


def ensureFolder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        else:
            pass


def locate(key, dict1, dict2, errmsg):
    if key in dict1:
        return dict1[key]
    else:
        if key in dict2:
            return dict2[key]
        else:
            ERROR(errmsg)
                

def setDefaultInMap(root, key, defaultValue):
    if not key in root:
        root[key] = defaultValue

def file2String(fname):
    with open(fname, 'r') as content_file:
        content = content_file.read()      
    return content

def findUpward(fileName, path):
    return findUpward2(fileName, path, path, 0)
 
def findUpward2(fileName, initial, location, cpt):
    x = os.path.join(location , fileName)
    if os.path.isfile(x):
        # Found !
        return x
    else:
        if location == "" or location == "/" :
            ERROR("Unable to locate a file named '{0}' in '{1}' and upward".format(fileName, initial))
        else:
            if cpt < 30:
                return findUpward2(fileName, initial, os.path.dirname(location), cpt + 1)
            else:
                raise Exception("Too many lookup while trying to locate '{}'".format(fileName))

REPOSITORIES="repositories"
HELPERS="helpers"
DATA="data"
CONFIG_FILE = "configFile"
FOLDER="folder"
SECURITY="security"
CONTEXT="context"
SECURITY_CONTEXTS="security_contexts"
CONFIG="config"
SECURITY_CONTEXT="security_context"
CLUSTER="cluster"
NAME="name"
HTTP_PROXIES="http_proxies"
PROXY_ID="proxy_id"
HTTPPROXIES="httpProxies"
FQDN="fqdn"
IP="ip"
NODES="nodes"


def lookupHttpProxy(model, proxyId, storeKey):
    setDefaultInMap(model["data"], HTTPPROXIES, {})
    if proxyId is None: 
        return
    if  HTTP_PROXIES not in model["config"]:
        ERROR("Missing {} in configuration file".format(HTTP_PROXIES))
    l = filter(lambda x: x[PROXY_ID] == proxyId, model["config"][HTTP_PROXIES])
    if len(l) > 1:
        ERROR("proxy_id '{}' is defined twice in configuration file!".format(proxyId))
    if len(l) != 1:
        ERROR("proxy_id '{}' is not defined in configuration file!".format(proxyId))
    model["data"][HTTPPROXIES][storeKey] = l[0]

def lookupRepository(model, mainEntry, configEntry=None, repoId=None):
    if configEntry == None:
        configEntry = mainEntry
    setDefaultInMap(model["data"], "repositories", {})
    if repoId == None:
        repoId = model["cluster"][mainEntry]["repo_id"] # Should be Required by schema
    if REPOSITORIES not in model["config"] or configEntry not in model["config"][REPOSITORIES]:
        ERROR("Missing {}.{} in configuration file".format(REPOSITORIES, configEntry))
    #print model["config"][REPOSITORIES][token]
    l = filter(lambda x: x["repo_id"] == repoId, model["config"][REPOSITORIES][configEntry])
    if len(l) > 1:
        ERROR("{} repo_id '{}' is defined twice in configuration file!".format(configEntry, repoId))
    if len(l) != 1:
        ERROR("{} repo_id '{}' is not defined in configuration file!".format(configEntry, repoId))
    model["data"][REPOSITORIES][configEntry] = l[0]
    
def lookupHelper(model, mainEntry, configEntry=None, helperId=None):
    if configEntry == None:
        configEntry = mainEntry
    setDefaultInMap(model["data"], HELPERS, {})
    if helperId is None:
        helperId = model["cluster"][mainEntry]["helper_id"] # Should be Required by schema
    if HELPERS not in model["config"] or configEntry not in model["config"][HELPERS]:
        ERROR("Missing {}.{} in configuration file".format(HELPERS, configEntry))
    #print model["config"][HELPERS][token]
    l = filter(lambda x: x["helper_id"] == helperId, model["config"][HELPERS][configEntry])
    if len(l) > 1:
        ERROR("{} helper_id '{}' is defined twice in configuration file!".format(configEntry, helperId))
    if len(l) != 1:
        ERROR("{} helper_id '{}' is not defined in configuration file!".format(configEntry, helperId))
    helper = l[0]
    helper[FOLDER] = appendPath(os.path.dirname(model[DATA][CONFIG_FILE]),  helper[FOLDER]) 
    model[DATA][HELPERS][configEntry] = helper

def lookupSecurityContext(model, mainEntry, configEntry=None):

    if configEntry == None:
        configEntry = mainEntry

    setDefaultInMap(model[DATA], SECURITY_CONTEXTS, {})

    context = model[CLUSTER][mainEntry][SECURITY_CONTEXT]

    if SECURITY_CONTEXTS not in model[CONFIG] or configEntry not in model[CONFIG][SECURITY_CONTEXTS]:
        ERROR("Missing {}.{} in configuration file".format(SECURITY_CONTEXTS, configEntry))

    # Considering name as identifier of the context
    l = filter(lambda x: x[NAME] == context, model[CONFIG][SECURITY_CONTEXTS][configEntry])

    if len(l) > 1:
        ERROR("{} context '{}' is defined twice in configuration file!".format(configEntry, context))
    if len(l) != 1:
        ERROR("{} context '{}' is not defined in configuration file!".format(configEntry, context))

    model[DATA][SECURITY_CONTEXTS][configEntry] = l[0]



def resolveDns(fqdn):
    try: 
        return socket.gethostbyname(fqdn)
    except socket.gaierror:
        return None

def resolveIps(model):
    nodeByIp = {}  # Just to check duplicated ip
    for node in model[CLUSTER][NODES]:
        ip = node[IP] = resolveDns(node[FQDN])
        if ip == None:
            ADD_ERROR("Unable to lookup IP for node '{0}' ({1})'.".format(node[NAME], node[FQDN]))
        else: 
            if ip not in nodeByIp:
                nodeByIp[ip] = node
            else:
                ERROR("Same IP ({}) used for both node '{}' and '{}'".format(ip, nodeByIp[ip][NAME], node[NAME]))
    FLUSH_ERROR()

    