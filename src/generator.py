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

import logging
import os
import stat
import jinja2
import sys
import traceback
from misc import ERROR, ensureFolder
import yaml
from vault import getVault
from jinja2.ext import Extension
from jinja2.exceptions import TemplateRuntimeError

logger = logging.getLogger("ezcluster.generator")


def to_pretty_yaml(a, **kw):
    """Make verbose, human readable yaml"""
    # transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=4, allow_unicode=True, default_flow_style=False, **kw)
    # return to_unicode(transformed)
    # return yaml.dump(a, width=120, default_flow_style=False,  canonical=False, default_style='"', tags=False, **kw)
    return yaml.dump(a, width=10240, indent=2, allow_unicode=True, default_flow_style=False, **kw)


def to_yaml(a, **kw):
    """Make yaml"""
    # transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=4, allow_unicode=True, default_flow_style=False, **kw)
    # return to_unicode(transformed)
    # return yaml.dump(a, width=120, default_flow_style=False,  canonical=False, default_style='"', tags=False, **kw)
    # return yaml.dump(a, width=10240,  indent=2, allow_unicode=True, default_flow_style=True, **kw)
    return yaml.dump(a, **kw)


# https://stackoverflow.com/questions/21778252/how-to-raise-an-exception-in-a-jinja2-macro
# https://github.com/duelafn/python-jinja2-apci

# {%% raise "An error message" %%}


class RaiseExtension(Extension):
    # This is our keyword(s):
    tags = {'raise'}

    # See also: jinja2.parser.parse_include()
    def parse(self, parser):
        # the first token is the token that started the tag. In our case we
        # only listen to "raise" so this will be a name token with
        # "raise" as value. We get the line number so that we can give
        # that line number to the nodes we insert.
        lineno = next(parser.stream).lineno

        # Extract the message from the template
        message_node = parser.parse_expression()

        return jinja2.nodes.CallBlock(
            self.call_method('_raise', [message_node], lineno=lineno),
            [], [], [], lineno=lineno
        )

    def _raise(self, msg, caller):
        raise TemplateRuntimeError(msg)


def indent(text, amount, ch=' '):
    padding = amount * ch
    return ''.join(padding + line for line in text.splitlines(True))


def encrypt(value, padding):
    vault = getVault()
    enc = vault.encrypt(value)
    return indent(enc, padding)


def concat(fileName, targetFile, startMark, endMark):
    result = ""
    for filePart in targetFile['fileParts']:
        if startMark and filePart['order'] != 0:
            result += "# ------------------------------------------------- Start of {0}/{1}-{2}\n".format(filePart.plugin, fileName, str(filePart.order))
        with open(filePart['name'], 'r') as f:
            result += f.read()
        if endMark and filePart['order'] != 999:
            result += "# --------------------------------------------------- End of {0}/{1}-{2}\n".format(filePart.plugin, fileName, str(filePart.order))
    return result


def generate2(targetFilePath, tmpl, model):
    ensureFolder(os.path.dirname(targetFilePath))
    result = None  # Just to remove a warning
    if isinstance(tmpl, jinja2.Template):
        try:
            result = tmpl.render(m=model)
        except jinja2.exceptions.TemplateRuntimeError as err:
            print('---------------------------------------------------------')
            traceback.print_exc(file=sys.stdout)
            print('---------------------------------------------------------')
            ERROR("Error in '{0}' file generation: {1}".format(targetFilePath, err.message))
    else:
        result = tmpl
    with open(targetFilePath, "w") as f:
        f.write(result)
    if targetFilePath.endswith(".sh"):
        cp = stat.S_IMODE(os.lstat(targetFilePath).st_mode)
        os.chmod(targetFilePath, cp | stat.S_IXUSR | (stat.S_IXGRP if cp & stat.S_IRGRP else 0) | (stat.S_IXOTH if cp & stat.S_IROTH else 0))
        logger.info("File '{0}' successfully generated as executable".format(targetFilePath))
    else:
        logger.info("File '{0}' successfully generated".format(targetFilePath))


def generate(targetFileByName, targetFolder, model, mark, dumper):
    j2env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        extensions=[RaiseExtension]
    )
    j2env.filters['to_pretty_yaml'] = to_pretty_yaml
    j2env.filters['to_yaml'] = to_yaml
    j2env.filters['encrypt'] = encrypt

    jj2env = jinja2.Environment(
        loader=jinja2.BaseLoader(),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        block_start_string="{%%",
        block_end_string="%%}",
        variable_start_string="{{{",
        variable_end_string="}}}",
        comment_start_string="{##",
        comment_end_string="##}",
        extensions=[RaiseExtension]
    )
    jj2env.filters['to_pretty_yaml'] = to_pretty_yaml
    jj2env.filters['to_yaml'] = to_yaml
    jj2env.filters['encrypt'] = encrypt

    generatedFiles = set()
    for targetFileName, targetFile in targetFileByName.items():
        ftype = targetFile["fileParts"][0]['type']  # plugin ensure type is same for all fileParts
        tmplSource = concat(targetFileName, targetFile, mark == "both" or mark == "start", mark == "both" or mark == "end")
        tmpl = None  # Just to remove a warning
        try:
            if ftype == "j2":
                tmpl = j2env.from_string(tmplSource)
            elif ftype == "jj2":
                tmpl = jj2env.from_string(tmplSource)
            elif ftype == "txt":
                tmpl = tmplSource
            else:
                ERROR("?? Unknown file type {0} on {1}".format(ftype, targetFileName))
        except jinja2.exceptions.TemplateSyntaxError as err:
            ERROR("Error in template built from '{0}'.\nLine {1}: {2}".format(str(targetFile), err.lineno, err))
        logger.debug(targetFileName)
        if dumper is not None:
            dumper.dumpTmpl(targetFileName, ftype, tmplSource)
        if "_node_" in targetFileName:
            for node in model['cluster']['nodes']:
                tgf = targetFileName.replace("_node_", node["name"])
                model['node'] = node
                targetFilePath = os.path.join(targetFolder, tgf)
                generate2(targetFilePath, tmpl, model)
                generatedFiles.add(targetFilePath)
        else:
            targetFilePath = os.path.join(targetFolder, targetFileName)
            generate2(targetFilePath, tmpl, model)
            generatedFiles.add(targetFilePath)
    # logger.debug(generatedFiles)
    # Will lookup file not generated, but presents in generation space
    for dirpath, dirnames, filenames in os.walk(targetFolder):  # @UnusedVariable
        for filename in filenames:
            f = os.path.join(dirpath, filename)
            # logger.debug(f)        
            if f not in generatedFiles:
                f2 = f[len(targetFolder):]
                if (not f2.startswith("/dump/")) and (not f2.startswith("/.vagrant/")) and (not f2.startswith("/.terraform/")) and (not f2.startswith("/terraform/")):
                    logger.warning("Zombie file '{0}'".format(f))
