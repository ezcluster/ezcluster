
import logging
import os
import yaml
from misc import ERROR
import ipaddress


logger = logging.getLogger("config.main")


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


def buildInfra(sourceFileDir):
    infraFile = findConfig('infra/sab-infra.yml', sourceFileDir, sourceFileDir, 0)
    infra = yaml.load(open(infraFile))
    # ---------------------------- Grooming
    infra['networkByName'] = {}
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
    for zone in infra['zones']:
        infra['zoneByName'][zone['name']] = zone
    del infra['zones']
    # ----------------------------
    infra['hostByName'] = {}
    for host in infra['hosts']:
        infra['hostByName'][host['name']] = host
    del infra['hosts']
    return infra

def buildRepositories(sourceFileDir):
    repoFile = findConfig('infra/sab-repositories.yml', sourceFileDir, sourceFileDir, 0)
    repos = yaml.load(open(repoFile))
    return repos



