


import os
import pprint

import misc

class Dumper:
    def __init__(self, location):
        self.folder = os.path.join(location, "dump")
        misc.ensureFolder(self.folder)
        
        
    def dump(self, fileName, model):
        out  = file(os.path.join(self.folder, fileName), "w")
        pp = pprint.PrettyPrinter(indent=2, stream=out)
        pp.pprint(model)
        out.close()
        
        