

import os
import errno

def ERROR(err):
    print "* * * * ERROR: {}".format(err)
    #raise Exception("xx")
    exit(1)


def ensureFolder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        else:
            pass
                