
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
    model['data']['kvmScriptsPath'] = appendPath(module.path, "scripts")
    # ------------------------------------------- Prepare memoryByHost
    memoryByHost = {}
    model['data']['memoryByHost'] = memoryByHost
    for hostName, _ in model['infra']["hostByName"].iteritems():
        memoryByHost[hostName] = {}
        memoryByHost[hostName]['sum'] = 0
        memoryByHost[hostName]['detail'] = {}
    # ------------------------------------------ Add role paths if there is any in cluster definition (May be useless now ?)
    if 'role_paths' in model['cluster']:
        for path in model['cluster']['role_paths']:
            path = appendPath(model['data']['sourceFileDir'], path)
            model['data']["rolePaths"].add(path)
    # ----------------------------------------- Handle roles
    model["data"]["roleByName"] = {}
    if 'roles' in model['cluster']:
        for ptrn in model["cluster"]["roles"]:
            role = copy.deepcopy(ptrn)
            model["data"]["roleByName"][role["name"]] = role
            # -------------- Zone
            zoneName = locate("zone", role, model["cluster"], "Role '{}': Missing zone definition (And no default value in cluster definition)".format(role["name"]))
            if zoneName not in model["infra"]["zoneByName"]:
                ERROR("Role '{}': Unknow zone '{}'".format(role["name"], zoneName))
            role["zone"] = zoneName
            zone = model["infra"]["zoneByName"][zoneName]
            role["network"] = model["infra"]["networkByName"][zone["network"]]
            # ------------- domain
            role['domain'] = locate("domain", role, model["cluster"], "Role '{}': Missing domain definition (And no default value in cluster definition)".format(role["name"]))
            # ------------- Template
            tmplName = locate("kvm_template", role, model["cluster"], "Role '{}': Missing kvm_template definition (And no default value in cluster definition)".format(role["name"]))
            if tmplName not in model["infra"]["kvmTemplateByName"]:
                ERROR("Role '{}': Unknow kvm_template '{}'".format(role["name"], tmplName))
            role["kvmTemplate"] = model["infra"]["kvmTemplateByName"][tmplName]
            # Handle root disk logical volumes
            if 'root_lvs' in role:
                vgSize = 0
                modifiedLv = set()
                for lv in role["root_lvs"]:
                    modifiedLv.add(lv["name"])
                    if "rootLvByName" not in role["kvmTemplate"] or lv["name"] not in role['kvmTemplate']['rootLvByName']:
                        ERROR("Role '{}': Logical volume '{}' does not exists in the template".format(role["name"], lv["name"]))
                    else:
                        templateLv = role['kvmTemplate']['rootLvByName'][lv["name"]]
                        lv['fstype'] = templateLv["fstype"]
                        lv["volgroup"] = role['kvmTemplate']['root_vg_name'] # Only one VG handled
                        vgSize += lv["size"]
                        if lv["size"] < templateLv["size"]:
                            ERROR("Role '{}': Logical volume '{}': size ({}GB) can't be lower than the one from template ({}GB) (Can't shrink LV)".format(role["name"], lv['name'], lv['size'], templateLv['size']))
                # To have accurate vg size, must add unmodified lv size
                for tmplLvName, tmplLv in role['kvmTemplate']['rootLvByName'].iteritems():
                    if tmplLvName not in modifiedLv:
                        vgSize += tmplLv['size'] 
                if vgSize >= role['kvmTemplate']["root_vg_size"]:
                    ERROR("Role '{}': Sum of all root LV must not exceed or equal template root PV ({} >= {})".format(role["name"], vgSize, role['kvmTemplate']["root_vg_size"]))
            # ------------------------------------ Data disks
            if "data_disks" in role:
                for i in range(0, len(role['data_disks'])):
                    role['data_disks'][i]['device'] = model['infra']['deviceFromIndex'][i]
                disksToMount = 0
                for d in role['data_disks']:
                    if "mount" in d:
                        disksToMount += 1
                role["disksToMountCount"] = disksToMount
            else:
                role["disksToMountCount"] = 0
    # ----------------------------------------- Handle nodes
    if 'nodes' in model['cluster']:
        nodeByIp = {}  # Just to check duplicated ip
        dataDisksByNode = {}
        model['data']['dataDisksByNode'] = dataDisksByNode
        for node in model['cluster']['nodes']:
            if not 'hostname' in node:
                node['hostname'] = node['name']
            if "vmname" not in node:
                node['vmname'] = model['cluster']['id'] + "_" + node['name']
            if node['role'] not in model['data']['roleByName']:
                ERROR("Node '{}' reference an unexisting role ({})".format(node["name"], node['role']))
            role =  model['data']['roleByName'][node['role']]
            node["fqdn"] = node['hostname'] + "." + role['domain']
            ip = node['ip'] = resolveDns(node['fqdn'])
            if ip == None:
                ERROR("Unable to lookup an IP for node '{0}' ({1})'.".format(node['name'], node['fqdn']))
            if ip not in nodeByIp:
                nodeByIp[ip] = node
            else:
                ERROR("Same IP ({}) used for both node '{}' and '{}'".format(ip, nodeByIp[ip]['name'], node['name']))
            network =  role["network"]
            node['network'] = network['name']
            if ipaddress.ip_address(u"" + ip) not in network['cidr']:
                ERROR("IP '{}' not in network '{}' for node {}".format(ip, network['name'], node['name']))
            if 'root_volume_index' in node:
                idx = node['root_volume_index']
            else:
                idx = 0
            if node['host'] not in model['infra']['hostByName']:
                ERROR("Node '{}' reference an unexisting host ({})".format(node["name"], node['host']))
            host = model['infra']['hostByName'][node['host']]
            nbrRootVolumes = len(host['root_volumes'])
            node['rootVolume'] = host['root_volumes'][idx % nbrRootVolumes]['path']
            # Handle data disk
            if 'data_disks' in role and len(role["data_disks"]) > 0:
                dataDisks = copy.deepcopy(role['data_disks'])
                nbrDataVolume = len(model['infra']['hostByName'][node['host']]['data_volumes'])
                if "data_volume_index" in node:
                    for i in range(len(dataDisks)):
                        dataDisks[i]['volume'] = model['infra']['hostByName'][node['host']]['data_volumes'][(i + node['data_volume_index']) % nbrDataVolume]['path']
                elif "data_volume_indexes" in node:
                    if len(node['data_volume_indexes']) != len(dataDisks):
                        ERROR("Node {0}: data_volume_indexes size ({1} != role.data_disks size ({2})".format(node['name'], node['data_volume_indexes'], len(dataDisks)))
                    for i in range(len(dataDisks)):
                        dataDisks[i]['volume'] = model['infra']['hostByName'][node['host']]['data_volumes'][node['data_volume_indexes'][i] % nbrDataVolume]['path']
                else:
                    ERROR("Node {0}: Either 'data_volume_index' or 'data_volume_indexes' must be defined!".format(node['name']))
                dataDisksByNode[node["name"]] = dataDisks
            memoryByHost[host['name']]['sum'] += role['memory']
            memoryByHost[host['name']]['detail'][node['name']] = role['memory']
        
    print "------------- Memory usage per host"
    l = list( model['data']['memoryByHost'].keys())
    for h in sorted(l):
        txt = "\t{}:{} (".format(h,  model['data']['memoryByHost'][h]['sum'])
        for alias in model['data']['memoryByHost'][h]['detail']:
            txt += " {}:{}".format(alias, model['data']['memoryByHost'][h]['detail'][alias])
        txt += " )"
        print txt




