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
import copy
from misc import ERROR, appendPath, locate
import socket
import ipaddress



def resolveDns(fqdn):
    try: 
        return socket.gethostbyname(fqdn)
    except socket.gaierror:
        return None

GROUP_BY_NAME="groupByName"
NODE_BY_NAME="nodeByName"
CLUSTER="cluster"
NODES="nodes"
GROUPS="groups"
ROLE_BY_NAME="roleByName"
NAME="name"
ROLE="role"
HOSTNAME="hostname"
DATA="data"
FQDN="fqdn"
IP="ip"
DOMAIN="domain"

def groom(plugin, model):
    if NODES not in model[CLUSTER]:
        model[CLUSTER][NODES] = []
    
    # ----------------------------------------- Handle roles
    model[DATA][ROLE_BY_NAME] = {}
    for rl in model[CLUSTER]["roles"]:
        role = copy.deepcopy(rl)
        model[DATA][ROLE_BY_NAME][role[NAME]] = role
        # --------------- Handle embedded nodes by pushing them back in cluster
        if NODES in role:
            for node in role[NODES]:
                if ROLE in node and node[ROLE] != role[NAME]:
                    ERROR("Node {}: role mismatch: '{}' != '{}'".format(node[NAME], node[ROLE], role[NAME]))
                node[ROLE] = role[NAME]
                model[CLUSTER][NODES].append(node)
            del role[NODES]
        role[NODES] = [] # Replace by an array of name
        # ------------- domain
        role[DOMAIN] = locate(DOMAIN, role, model[CLUSTER], "Role '{}': Missing domain definition (And no default value in cluster definition)".format(role[NAME]))
    # ----------------------------------------- Handle nodes
    nodeByIp = {}  # Just to check duplicated ip
    model[DATA][GROUP_BY_NAME] = {}
    model[DATA][NODE_BY_NAME] = {}
    for node in model[CLUSTER][NODES]:
        if node[NAME] in  model[DATA][NODE_BY_NAME]:
            ERROR("Node '{}' is defined twice!".format(node[NAME]))
        model[DATA][NODE_BY_NAME][node[NAME]] = node
        if not HOSTNAME in node:
            node[HOSTNAME] = node[NAME]
        if ROLE not in node:
            ERROR("Node '{}': Missing role definition".format(node[NAME]))
        if node[ROLE] not in model[DATA][ROLE_BY_NAME]:
            ERROR("Node '{}' reference an unexisting role ({})".format(node[NAME], node[ROLE]))
        role =  model[DATA][ROLE_BY_NAME][node[ROLE]]
        role[NODES].append(node[NAME])
        node[FQDN] = (node[HOSTNAME]  + "." + role[DOMAIN]) if (role[DOMAIN] != None) else node[HOSTNAME]
        ip = node[IP] = resolveDns(node[FQDN])
        if ip == None:
            ERROR("Unable to lookup an IP for node '{0}' ({1})'.".format(node[NAME], node[FQDN]))
        if ip not in nodeByIp:
            nodeByIp[ip] = node
        else:
            ERROR("Same IP ({}) used for both node '{}' and '{}'".format(ip, nodeByIp[ip][NAME], node[NAME]))
        # Handle ansible groups binding
        if GROUPS in node:
            for grp in node[GROUPS]:
                if grp not in  model[DATA][GROUP_BY_NAME]:
                    model[DATA][GROUP_BY_NAME][grp] = []
                model[DATA][GROUP_BY_NAME][grp].append(node[NAME])
    
    # -------------------------- Build ansible groups
    for _, role in model[DATA][ROLE_BY_NAME].iteritems():
        # ---------------- Handle ansible groups
        if not GROUPS in role:
            role[GROUPS] = [ role[NAME] ]
        for grp in role[GROUPS]:
            if grp not in  model[DATA][GROUP_BY_NAME]:
                 model[DATA][GROUP_BY_NAME][grp] = []
            for nodeName in role[NODES]:
                model[DATA][GROUP_BY_NAME][grp].append(nodeName)
    
    return True # Always enabled


