
import logging
import os
import yaml
from misc import ERROR, appendPath
import ipaddress
from pykwalify.core import Core as kwalify


logger = logging.getLogger("ezcluster.config")


# TODO: Schema validation
        
def findConfig(fileName, initial, location, cpt):
    x = os.path.join(location , fileName)
    if os.path.isfile(x):
        # Found !
        logger.info("Use '{0}' as config file".format(x))
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
    # ---------------------------- Grooming
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
            infra['kvmTemplateByName'][template['name']] = template
        del infra['kvm_templates']
    return infra

def buildRepositories(sourceFileDir):
    repoFile = findConfig('infra/sab-repositories.yml', sourceFileDir, sourceFileDir, 0)
    repos = yaml.load(open(repoFile))
    return repos



