
import os
import misc

def groom(module, model):
    if not "rolePaths" in model['data']:
        model['data']["rolePaths"] = set()
    if 'role_paths' in model['cluster']:
        for path in model['cluster']['role_paths']:
            path = misc.appendPath(model['data']['sourceFileDir'], path)
            model['data']["rolePaths"].add(path)
