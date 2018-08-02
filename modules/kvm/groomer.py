
import logging
import os
import copy
from misc import ERROR, appendPath, locate
import socket
import ipaddress
import yaml
from pykwalify.core import Core as kwalify



loggerConfig = logging.getLogger("ezcluster.config")

      
def findConfig(fileName, initial, location, cpt):
    x = os.path.join(location , fileName)
    if os.path.isfile(x):
        # Found !
        loggerConfig.info("Use '{0}' as config file".format(x))
        return x
        #return edict(yaml.load(open(x)))
    else:
        if location == "" or location == "/" :
            ERROR("Unable to locate a {0} file in '{1}' and upward".format(fileName, initial))
        else:
            if cpt < 20:
                return findConfig(fileName, initial, os.path.dirname(location), cpt + 1)
            else:
                raise Exception("Too many lookup")


def buildInfra(mydir, sourceFileDir):
    infraFile = findConfig('infra/sab-infra.yml', sourceFileDir, sourceFileDir, 0)
    infra = yaml.load(open(infraFile))
    schema = yaml.load(open(os.path.join(mydir, "./schemas/infra.yml")))
    k = kwalify(source_data = infra, schema_data=schema)
    k.validate(raise_exception=False)
    if len(k.errors) != 0:
        ERROR("Problem {0}: {1}".format(infraFile, k.errors))
    # ---------------------------- Network Grooming
    infra['networkByName'] = {}
    if 'networks' in infra:
        for network in infra['networks']:
            network['cidr'] = ipaddress.IPv4Network(u"" + network['base'] + "/" + network['netmask'], strict=True) 
            if ipaddress.ip_address(u"" + network['gateway']) not in network['cidr']:
                ERROR("Gateway '{0}' not in network {1}".format(network['gateway'], network))
            if ipaddress.ip_address(u"" + network['broadcast']) not in network['cidr']:
                ERROR("Broadcast '{0}' not in network {1}".format(network['broadcast'], network))
            infra['networkByName'][network['name']] = network
        del infra['networks']  # All network access by networkByName
    # ----------------------------
    infra['zoneByName'] = {}
    if 'zones' in infra:
        for zone in infra['zones']:
            infra['zoneByName'][zone['name']] = zone
        del infra['zones']
    # ----------------------------
    infra['hostByName'] = {}
    if 'hosts' in infra:
        for host in infra['hosts']:
            infra['hostByName'][host['name']] = host
        del infra['hosts']
    # ----------------------
    infra['kvmTemplateByName'] = {}
    if 'kvm_templates' in infra:
        for template in infra["kvm_templates"]:
            if 'build_key_pair' in template:
                template['build_key_pair'] = appendPath(os.path.dirname(infraFile), template['build_key_pair'])
            if "root_lvs" in template:
                rootLvByName = {}
                for lv in template['root_lvs']:
                    rootLvByName[lv["name"]] = lv
                    del lv["name"]
                template['rootLvByName'] = rootLvByName
                del template["root_lvs"]
            infra['kvmTemplateByName'][template['name']] = template
        del infra['kvm_templates']
    return infra

def buildRepositories(sourceFileDir):
    repoFile = findConfig('infra/sab-repositories.yml', sourceFileDir, sourceFileDir, 0)
    repos = yaml.load(open(repoFile))
    return repos

def groom(module, model):
    if 'core' not in model["cluster"]["modules"]:
        ERROR("Module 'core' is mandatory before module 'kvm'")
    
    infra = buildInfra(module.path, model['data']['sourceFileDir'])
    model['infra'] = infra
    
    repositories = buildRepositories(model['data']['sourceFileDir'])
    model['repositories'] = repositories
    
    model['data']['kvmScriptsPath'] = appendPath(module.path, "scripts")
    # ------------------------------------------- Prepare memoryByHost
    memoryByHost = {}
    model['data']['memoryByHost'] = memoryByHost
    for hostName, _ in model['infra']["hostByName"].iteritems():
        memoryByHost[hostName] = {}
        memoryByHost[hostName]['sum'] = 0
        memoryByHost[hostName]['detail'] = {}
    # ----------------------------------------- Handle roles
    for rl in model["cluster"]["roles"]:
        role = model["data"]["roleByName"][rl["name"]]
        # -------------- Zone
        zoneName = locate("zone", role, model["cluster"], "Role '{}': Missing zone definition (And no default value in cluster definition)".format(role["name"]))
        if zoneName not in model["infra"]["zoneByName"]:
            ERROR("Role '{}': Unknow zone '{}'".format(role["name"], zoneName))
        role["zone"] = zoneName
        zone = model["infra"]["zoneByName"][zoneName]
        role["network"] = model["infra"]["networkByName"][zone["network"]]
        # ------------- Template
        tmplName = locate("kvm_template", role, model["cluster"], "Role '{}': Missing kvm_template definition (And no default value in cluster definition)".format(role["name"]))
        if tmplName not in model["infra"]["kvmTemplateByName"]:
            ERROR("Role '{}': Unknow kvm_template '{}'".format(role["name"], tmplName))
        role["kvmTemplate"] = model["infra"]["kvmTemplateByName"][tmplName]
        # ---------------- Handle root disk logical volumes
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
    dataDisksByNode = {}

    model['data']['dataDisksByNode'] = dataDisksByNode
    for node in model['cluster']['nodes']:
        if "vmname" not in node:
            node['vmname'] = model['cluster']['id'] + "_" + node['name']
        role =  model['data']['roleByName'][node['role']]
        network =  role["network"]
        node['network'] = network['name']
        if ipaddress.ip_address(u"" + node['ip']) not in network['cidr']:
            ERROR("IP '{}' not in network '{}' for node {}".format(node['ip'], network['name'], node['name']))
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

def dump(module, model, dumper):
    dumper.dump("infra.json", model['infra'])
    dumper.dump("repositories.json", model['repositories'])
    



