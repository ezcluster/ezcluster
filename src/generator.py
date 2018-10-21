import logging
import os
import jinja2
import sys, traceback
from misc import ERROR, ensureFolder
import yaml

logger = logging.getLogger("ezcluster.generator")



def to_nice_yaml(a, **kw):
    '''Make verbose, human readable yaml'''
    #transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=4, allow_unicode=True, default_flow_style=False, **kw)
    #return to_unicode(transformed)
    #return yaml.dump(a, width=120, default_flow_style=False,  canonical=False, default_style='"', tags=False, **kw)
    return yaml.dump(a, width=10240,  indent=4, allow_unicode=True, default_flow_style=False, **kw)


def to_yaml(a, **kw):
    '''Make yaml'''
    #transformed = yaml.dump(a, Dumper=AnsibleDumper, indent=4, allow_unicode=True, default_flow_style=False, **kw)
    #return to_unicode(transformed)
    #return yaml.dump(a, width=120, default_flow_style=False,  canonical=False, default_style='"', tags=False, **kw)
    #return yaml.dump(a, width=10240,  indent=2, allow_unicode=True, default_flow_style=True, **kw)
    return yaml.dump(a, **kw)



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
    if isinstance(tmpl,  jinja2.Template):
        try:
            result = tmpl.render(m=model)
        except jinja2.exceptions.TemplateRuntimeError as err:
            print '---------------------------------------------------------'
            traceback.print_exc(file=sys.stdout)
            print '---------------------------------------------------------'
            ERROR("Error in '{0}' file generation: {1}".format(targetFilePath, err.message))
    else:
        result = tmpl
    with open(targetFilePath, "w") as f:
        f.write(result) 
    logger.info("File '{0}' successfully generated".format(targetFilePath))

def generate(targetFileByName, targetFolder, model, mark):
    j2env = jinja2.Environment(
            loader = jinja2.BaseLoader(), 
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
        )
    j2env.filters['to_nice_yaml'] = to_nice_yaml
    j2env.filters['to_yaml'] = to_yaml
    
    jj2env = jinja2.Environment(
            loader = jinja2.BaseLoader(), 
            undefined=jinja2.StrictUndefined,
            trim_blocks=True,
            block_start_string="{%%",
            block_end_string="%%}",
            variable_start_string="{{{",
            variable_end_string="}}}",
            comment_start_string="{{#",
            comment_end_string="#}}"
        )
    jj2env.filters['to_nice_yaml'] = to_nice_yaml
    jj2env.filters['to_yaml'] = to_yaml
     
    generatedFiles = set()
    for targetFileName, targetFile in targetFileByName.iteritems():
        ftype = targetFile["fileParts"][0]['type']  # plugin ensure type is same for all fileParts
        tmplSource = concat(targetFileName, targetFile, mark == "both" or mark == "start", mark == "both" or mark == "end")
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
        # logger.debug(tmpl)
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
                logger.warning("Zombie file '{0}'".format(f))
        
        
    
