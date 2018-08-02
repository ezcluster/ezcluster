
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


def groom(module, model):
    if 'nodes' not in model["cluster"]:
        model['cluster']['nodes'] = []
    
    # ----------------------------------------- Handle roles
    model["data"]["roleByName"] = {}
    for rl in model["cluster"]["roles"]:
        role = copy.deepcopy(rl)
        model["data"]["roleByName"][role["name"]] = role
        # --------------- Handle embedded nodes by pushing them back in cluster
        if 'nodes' in role:
            for node in role["nodes"]:
                if 'role' in node and node['role'] != role['name']:
                    ERROR("Node {}: role mismatch: '{}' != '{}'".format(node["name"], node['role'], role["name"]))
                node["role"] = role["name"]
                model["cluster"]["nodes"].append(node)
            del role['nodes']
        role['nodes'] = [] # Replace by an array of name
        # ------------- domain
        role['domain'] = locate("domain", role, model["cluster"], "Role '{}': Missing domain definition (And no default value in cluster definition)".format(role["name"]))
    # ----------------------------------------- Handle nodes
    nodeByIp = {}  # Just to check duplicated ip
    nodeByName = {} # Currently, just to check duplicated name. May be set in 'data' if usefull
    model["data"]["groupByName"] = {}

    for node in model['cluster']['nodes']:
        if node['name'] in nodeByName:
            ERROR("Node '{}' is defined twice!".format(node['name']))
        nodeByName[node['name']] = node
        if not 'hostname' in node:
            node['hostname'] = node['name']
        if 'role' not in node:
            ERROR("Node '{}': Missing role definition".format(node["name"]))
        if node['role'] not in model['data']['roleByName']:
            ERROR("Node '{}' reference an unexisting role ({})".format(node["name"], node['role']))
        role =  model['data']['roleByName'][node['role']]
        role['nodes'].append(node["name"])
        node["fqdn"] = node['hostname'] + "." + role['domain']
        ip = node['ip'] = resolveDns(node['fqdn'])
        if ip == None:
            ERROR("Unable to lookup an IP for node '{0}' ({1})'.".format(node['name'], node['fqdn']))
        if ip not in nodeByIp:
            nodeByIp[ip] = node
        else:
            ERROR("Same IP ({}) used for both node '{}' and '{}'".format(ip, nodeByIp[ip]['name'], node['name']))
        # Handle ansible groups binding
        if "groups" in node:
            for grp in node["groups"]:
                if grp not in  model["data"]["groupByName"]:
                    model["data"]["groupByName"][grp] = []
                model["data"]["groupByName"][grp].append(node["name"])
    # -------------------------- Build ansible groups
    for _, role in model['data']['roleByName'].iteritems():
        # ---------------- Handle ansible groups
        if not 'groups' in role:
            role['groups'] = [ role["name"] ]
        for grp in role["groups"]:
            if grp not in  model["data"]["groupByName"]:
                 model["data"]["groupByName"][grp] = []
            for nodeName in role['nodes']:
                model["data"]["groupByName"][grp].append(nodeName)
    



