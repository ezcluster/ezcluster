# Copyright (C) 2018 BROADSoftware
#
# This file is part of EzCluster
#
# EzCluster is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EzCluster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with EzCluster.  If not, see <http://www.gnu.org/licenses/lgpl-3.0.html>.

import os
import pprint

import misc

class Dumper:
    def __init__(self, location, unsafe):
        self.folder = os.path.join(location, "dump")
        self.unsafe = unsafe
        misc.ensureFolder(self.folder)
        
        
        
    def dump(self, fileName, model):
        out  = file(os.path.join(self.folder, fileName), "w")
        pp = pprint.PrettyPrinter(indent=2, stream=out)
        pp.pprint(model)
        out.close()
        
        
    def dumpTmpl(self, fileName, tmplType, string):
        fname = os.path.join(self.folder, "tmpls", fileName + "." + tmplType)
        misc.ensureFolder(os.path.dirname(fname))
        with open(fname, "w") as f:
            f.write(string) 

        
        