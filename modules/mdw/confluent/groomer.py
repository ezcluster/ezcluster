



def groom(module, model):
    for node in model['cluster']['nodes']:
        if "kafka_log_dirs" in node:
            if len(node["kafka_log_dirs"]) == 0:
                del(node["kafka_log_dirs"])
        else:
            if "kafka_log_dirs" in model["data"]["roleByName"][node["role"]]:
                node["kafka_log_dirs"] = model["data"]["roleByName"][node["role"]]["kafka_log_dirs"]
    
