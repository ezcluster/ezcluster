

import copy
from misc import ERROR
from schema import schemaMerge


CLUSTER="cluster"
NODES="nodes"
ELASTICSEARCH="elasticsearch"
ROLE="role"
DATA="data"
ROLE_BY_NAME="roleByName"
_ELASTICSEARCH_="_elasticsearch_"
NAME="name"

def groom(module, model):
    # Will merge elasticsearch vars from:
    # - node
    # - group
    # - global
    for node in model[CLUSTER][NODES]:
        # Get the node specific value
        if ELASTICSEARCH in node:
            if not isinstance(node[ELASTICSEARCH], dict):
                ERROR("Invalid node definition ('{}'):  '{}' is not a dictionary".format(node[NAME], ELASTICSEARCH))
            else:
                map = copy.deepcopy(node[ELASTICSEARCH])
        else:
            map = {}
        # Add the role specific value
        if ROLE in node:
            role = model[DATA][ROLE_BY_NAME][node[ROLE]]
            if ELASTICSEARCH in role:
                if not isinstance(role[ELASTICSEARCH], dict):
                    ERROR("Invalid role definition ('{}'):  '{}' is not a dictionary".format(role[NAME], ELASTICSEARCH))
                else:
                    map = schemaMerge(map, role[ELASTICSEARCH])
        # And add global value
        if ELASTICSEARCH in model[CLUSTER]:
            if not isinstance(model[CLUSTER][ELASTICSEARCH], dict):
                ERROR("Invalid global '{}' definition:  not a dictionary".format(ELASTICSEARCH))
            else:
                map = schemaMerge(map, model[CLUSTER][ELASTICSEARCH])
        node[_ELASTICSEARCH_] = map
        
        
            
