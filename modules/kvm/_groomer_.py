
import os
import copy
from misc import ERROR, appendPath
import socket
import ipaddress

def locate(key, dict1, dict2, errmsg):
    if key in dict1:
        return dict1[key]
    else:
        if key in dict2:
            return dict2[key]
        else:
            ERROR(errmsg)



def resolveDns(fqdn):
    try: 
        return socket.gethostbyname(fqdn)
    except socket.gaierror:
        return None

def groom(module, model):
    model['data']['kvmScriptsPath'] = appendPath(module.path, "_scripts")
    # ----------------------------------------- Handle patterns
    model["data"]["patternByName"] = {}
    if 'patterns' in model['cluster']:
        for ptrn in model["cluster"]["patterns"]:
            pattern = copy.deepcopy(ptrn)
            model["data"]["patternByName"][pattern["name"]] = pattern
            # -------------- Zone
            zoneName = locate("zone", pattern, model["cluster"], "Pattern '{}': Missing zone definition (And no default value in cluster definition)".format(pattern["name"]))
            if zoneName not in model["infra"]["zoneByName"]:
                ERROR("Pattern '{}': Unknow zone '{}'".format(pattern["name"], zoneName))
            pattern["zone"] = zoneName
            zone = model["infra"]["zoneByName"][zoneName]
            pattern["network"] = model["infra"]["networkByName"][zone["network"]]
            # ------------- domain
            pattern['domain'] = locate("domain", pattern, model["cluster"], "Pattern '{}': Missing domain definition (And no default value in cluster definition)".format(pattern["name"]))
            # ------------- Template
            tmplName = locate("kvm_template", pattern, model["cluster"], "Pattern '{}': Missing kvm_template definition (And no default value in cluster definition)".format(pattern["name"]))
            if tmplName not in model["infra"]["kvmTemplateByName"]:
                ERROR("Pattern '{}': Unknow kvm_template '{}'".format(pattern["name"], tmplName))
            pattern["kvmTemplate"] = model["infra"]["kvmTemplateByName"][tmplName]
            # Check root disk capacity
            rd = pattern['root_disk']
            s = rd["slash"] + rd["varlog"] + rd["swap"]
            if s  >= pattern['kvmTemplate']["root_physical_volume_size_gb"]:
                ERROR("Sum of all root_disk LV must not exceed or equal template root PV ({} >= {})".format(s, pattern['kvmTemplate']["root_physical_volume_size_gb"]))
    
    
    # ----------------------------------------- Handle patterns
    if 'nodes' in model['cluster']:
        nodeByIp = {}
        for node in model['cluster']['nodes']:
            if not 'hostname' in node:
                node['hostname'] = node['name']
            if "vmname" not in node:
                node['vmname'] = model['cluster']['id'] + "_" + node['name']
            if node['host'] not in model['infra']['hostByName']:
                ERROR("Node '{}' reference an unexisting host ({})".format(node["name"], node['host']))
            if node['pattern'] not in model['data']['patternByName']:
                ERROR("Node '{}' reference an unexisting pattern ({})".format(node["name"], node['pattern']))
            pattern =  model['data']['patternByName'][node['pattern']]
            node["fqdn"] = node['hostname'] + "." + pattern['domain']
            ip = node['ip'] = resolveDns(node['fqdn'])
            if ip == None:
                ERROR("Unable to lookup an IP for node '{0}' ({1})'.".format(node['name'], node['fqdn']))
            if ip not in nodeByIp:
                nodeByIp[ip] = node
            else:
                ERROR("Same IP ({}) used for both node '{}' and '{}'".format(ip, nodeByIp[ip]['name'], node['name']))
            network =  pattern["network"]
            node['network'] = network['name']
            if ipaddress.ip_address(u"" + ip) not in network['cidr']:
                ERROR("IP '{}' not in network '{}' for node {}".format(ip, network['name'], node['name']))

            


