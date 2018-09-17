
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


def groom(module, model):
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
        role['domain'] = locate("domain", role, model[CLUSTER], "Role '{}': Missing domain definition (And no default value in cluster definition)".format(role[NAME]))
    # ----------------------------------------- Handle nodes
    nodeByIp = {}  # Just to check duplicated ip
    nodeByName = {} # Currently, just to check duplicated name. May be set in DATA if usefull
    model[DATA][GROUP_BY_NAME] = {}

    for node in model[CLUSTER][NODES]:
        if node[NAME] in nodeByName:
            ERROR("Node '{}' is defined twice!".format(node[NAME]))
        nodeByName[node[NAME]] = node
        if not HOSTNAME in node:
            node[HOSTNAME] = node[NAME]
        if ROLE not in node:
            ERROR("Node '{}': Missing role definition".format(node[NAME]))
        if node[ROLE] not in model[DATA][ROLE_BY_NAME]:
            ERROR("Node '{}' reference an unexisting role ({})".format(node[NAME], node[ROLE]))
        role =  model[DATA][ROLE_BY_NAME][node[ROLE]]
        role[NODES].append(node[NAME])
        node[FQDN] = node[HOSTNAME] + "." + role['domain']
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
    



