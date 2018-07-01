

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
                