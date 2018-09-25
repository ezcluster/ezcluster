
import os
import copy
import yaml
from misc import ERROR
from schema import schemaMerge


CLUSTER="cluster"
ELASTICSEARCH="elasticsearch"
ROLE="role"
DATA="data"
NAME="name"
ES_NODES="es_nodes"
ROLES="roles"
ESNODES="esNodes"
ES_CONFIG="es_config"
NODE_MASTER="node.master"
VARS="vars"
ES_INSTANCE_NAME="es_instance_name"
_ELASTICSEARCH_="_elasticsearch_"
NODES="nodes"
GROUP_BY_NAME="groupByName"

def groom(module, model):
    
    f = os.path.join(module.path, "default.yml")
    if os.path.exists(f):
        base = yaml.load(open(f))
    else:
        base = {}
        
    model[DATA][ESNODES] = []        
    """ 
    For each es_node, will merge elasticsearch vars from:
    - Module default configuration file
    - global from cluster definition file
    - parent role
    - es_node """
    for role in model[CLUSTER][ROLES]:
        if ES_NODES in role:
            index = -1
            for esnode in role[ES_NODES]:
                index += 1
                map = copy.deepcopy(base)
                # Add global value
                if ELASTICSEARCH in model[CLUSTER]:
                    if not isinstance(model[CLUSTER][ELASTICSEARCH], dict):
                        ERROR("Invalid global '{}' definition:  not a dictionary".format(ELASTICSEARCH))
                    else:
                        map = schemaMerge(map, model[CLUSTER][ELASTICSEARCH])
                # Add the role specific value
                if ELASTICSEARCH in role:
                    if not isinstance(role[ELASTICSEARCH], dict):
                        ERROR("Invalid role definition ('{}'):  '{}' is not a dictionary".format(role[NAME], ELASTICSEARCH))
                    else:
                        map = schemaMerge(map, role[ELASTICSEARCH])
                # And get the es_node specific value
                if not isinstance(esnode, dict):
                    ERROR("Invalid es_node definition in role '{}':  item#{} is not a dictionary".format(role[NAME], index))
                else:
                    map = schemaMerge(map, esnode)
                if not ES_CONFIG in map or not NODE_MASTER in map[ES_CONFIG]:
                    ERROR("Invalid es_node definition in role '{}, item#{}: es_config.'node.master' must be defined".format(role[NAME], index))
                if not ES_INSTANCE_NAME in map:
                    ERROR("Invalid es_node definition in role '{}, item#{}: es_instance_name must be defined".format(role[NAME], index))
                esn = {}
                esn[ROLE] = role[NAME]
                esn[VARS] = map
                model[DATA][ESNODES].append(esn)
    # We must arrange for master nodes to be deployed first.
    model[DATA][ESNODES].sort(key=keyFromEsNode, reverse=False)   
    # We need to define an ansible group "_elasticsearch_" hosting all nodes with elasticsearch installed
    elasticGroup = []
    for role in model[CLUSTER][ROLES]:
        if ES_NODES in role:
            for node in role[NODES]:
                elasticGroup.append(node[NAME])
    model[DATA][GROUP_BY_NAME][_ELASTICSEARCH_] = elasticGroup
    


def keyFromEsNode(esNode):
    return "0" if esNode[VARS][ES_CONFIG][NODE_MASTER] else "1"       
        
            
