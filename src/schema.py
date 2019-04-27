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


import yaml
import os

"""
From http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
Modified for merging sequence, which are only one elements. So, must merge inner (mapping) items
"""
class YamlReaderError(Exception):
    pass

def schemaMerge(a, b):
    """merges b into a and return merged result
    NOTE: tuples and arbitrary objects are not handled as it is totally ambiguous what should happen"""
    if b is None:
        return a
    key = None
    # ## debug output
    # sys.stderr.write("DEBUG: %s to %s\n" %(b,a))
    try:
        if a is None or isinstance(a, str) or isinstance(a, unicode) or isinstance(a, int) or isinstance(a, long) or isinstance(a, float):
            # border case for first run or if a is a primitive
            a = b
        elif isinstance(a, list):
            # lists can be only appended
            if isinstance(b, list):
                # merge lists
                #a.extend(b)
                # Specific to kwalify schema description: Sequence are alwoys on item.
                schemaMerge(a[0], b[0]) 
            else:
                # append to list
                a.append(b)
        elif isinstance(a, dict):
            # dicts must be merged
            if isinstance(b, dict):
                for key in b:
                    if key in a:
                        a[key] = schemaMerge(a[key], b[key])
                    else:
                        a[key] = b[key]
            else:
                raise YamlReaderError('Cannot merge non-dict "%s" into dict "%s"' % (b, a))
        else:
            raise YamlReaderError('NOT IMPLEMENTED "%s" into "%s"' % (b, a))
    except TypeError, e:
        raise YamlReaderError('TypeError "%s" in key "%s" when merging "%s" into "%s"' % (e, key, b, a))
    return a


def buildSchema(mydir, plugins):
    schema = yaml.load(open(os.path.join(mydir, "./schemas/root.yml")), Loader=yaml.SafeLoader)
    for plugin in plugins:
        schema = schemaMerge(schema, plugin.getSchema())
    return schema


# We must take all possible schema in account, on all modules path, as configuration is independant of a specific set of modules
def buildConfigSchema(mydir, pluginsPaths):
    schema = yaml.load(open(os.path.join(mydir, "./schemas/config-root.yml")), Loader=yaml.SafeLoader)
    safeSchema = yaml.load(open(os.path.join(mydir, "./schemas/safe-config-root.yml")), Loader=yaml.SafeLoader)
    for path in pluginsPaths:
        for d in os.listdir(path):
            f = os.path.join(path, d, "config-schema.yml")
            if os.path.exists(f):
                schema = schemaMerge(schema, yaml.load(open(f), Loader=yaml.SafeLoader))
            sf = os.path.join(path, d, "safe-config-schema.yml")
            if os.path.exists(sf):
                safeSchema = schemaMerge(safeSchema, yaml.load(open(sf), Loader=yaml.SafeLoader))
    return schema, safeSchema



    
