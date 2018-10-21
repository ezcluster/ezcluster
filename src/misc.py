

import os
import errno

def ERROR(err):
    print "* * * * ERROR: {}".format(err)
    #raise Exception("xx")
    exit(1)

def appendPath(p1, p2):
    if os.path.isabs(p2):
        return p2
    else:
        return os.path.normpath(os.path.join(p1, p2))


def ensureFolder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        else:
            pass


def locate(key, dict1, dict2, errmsg):
    if key in dict1:
        return dict1[key]
    else:
        if key in dict2:
            return dict2[key]
        else:
            ERROR(errmsg)
                

def setDefaultInMap(root, key, defaultValue):
    if not key in root:
        root[key] = defaultValue

def findUpward(fileName, path):
    return findUpward2(fileName, path, path, 0)
 
def findUpward2(fileName, initial, location, cpt):
    x = os.path.join(location , fileName)
    if os.path.isfile(x):
        # Found !
        return x
    else:
        if location == "" or location == "/" :
            ERROR("Unable to locate a {0} file in '{1}' and upward".format(fileName, initial))
        else:
            if cpt < 30:
                return findUpward2(fileName, initial, os.path.dirname(location), cpt + 1)
            else:
                raise Exception("Too many lookup while trying to locate '{}'".format(fileName))
