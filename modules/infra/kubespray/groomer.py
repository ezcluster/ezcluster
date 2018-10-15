

from misc import ERROR, setDefaultInMap, appendPath

def groom(module, model):
    repo_folder = appendPath(model["data"]["sourceFileDir"],  model["cluster"]["kubespray"]["repo_folder"]) 
    model["cluster"]["kubespray"]["repo_folder"] = repo_folder
    model["data"]["rolePaths"].add(appendPath(repo_folder, "roles"))
