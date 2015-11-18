from mongoengine import *
from datetime import datetime
import json, time
import agent_utils
from agent_types import *
import models_route as route

connect("MoniterDB")
log = agent_utils.getLogger()

# 0. METRIC models
class MetricModel(DynamicDocument):
    name = StringField(max_length=300)
    timestamp = DateTimeField()
    value = DynamicField()
    # tags: will be dynamically added
    
class ConfigModel(DynamicDocument):
    name = StringField(max_length=300)
    timestamp = DateTimeField()
    value = DynamicField()
    
class CurrentModel(DynamicDocument):
    name = StringField(max_length=300)
    timestamp = DateTimeField()
    value = DynamicField()

# 1. STATIC INFO models
# user and group info
class UserInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) #     
    type = StringField(max_length=200) # user or group
    inventory = ListField(StringField(max_length=300)) # different from subitems(sub objects)

# InventoryModel stores entity index and info 
class InventoryInfoModel(DynamicDocument):
    name = StringField(max_length=300)
    host = StringField(max_length=300) # changed Jul 28: host uid(mac)
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) #     
    display_name = StringField(max_length=300)
    timestamp = DateTimeField()
   
class CurrentInfoModel(DynamicDocument):
    name = StringField(max_length=300)
    host = StringField(max_length=300) # changed Jul 28: host uid(mac)
    display_name = StringField(max_length=300)
    timestamp = DateTimeField()   
 
'''
# Hostinfo model
class HostInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) #     
    address = StringField(max_length=32)

class VMInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) #     
    address = StringField(max_length=32)
    vmid = StringField(max_length=300)
    
class ClusterInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) #     
    
class ServiceInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) # 
'''
    
class MetricInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    type = StringField(max_length=300)
    description = StringField()
    interval = IntField()
    cmd = StringField()
    
    @classmethod
    def from_metric_desc(cls, met):
        pass
        
    def to_metric_desc(self):
        pass

class PluginInfoModel(DynamicDocument):
    uuid = StringField(max_length=300, primary_key=True)
    name = StringField(max_length=300)
    parent = StringField(max_length=300) # parent entity
    owner = StringField(max_length=300) # owner(user/group)
    subitems = ListField(StringField(max_length=300)) # 
    
    description = StringField()
    type = StringField(max_length=300)
    cmd_list = DictField()
    metrics = ListField(ReferenceField(MetricInfoModel))
    
    def from_plugin_desc(cls, p):
        pass
        
    def to_plugin_desc(self):
        pass
    
# 2. RUNTIME STATUS models
# runtime metric: tags can be dynamically added to this schema
class PluginModel(DynamicDocument):
    info = ReferenceField(PluginInfoModel)
    # user = ReferenceField(UserModel)
    pid = IntField()
    uptime = DateTimeField()

class AgentModel(DynamicDocument): 
    host = StringField(max_length=300)
    # user = ReferenceField(UserModel)
    pid = IntField()
    uptime = DateTimeField()
    heartbeat = DateTimeField()
    plugins = ListField(ReferenceField(PluginModel))
    

# 3. (TODO) STAT models
# preserves some statistics about entities

# 4. (TODO) Warning rules model
class RuleModel(DynamicDocument):
    range = DictField()         # criteria to query entities applying this rule
    description = StringField()
    level = StringField()       # error/warning level
    script = StringField()      # judge rules(todo)
    
# 5. backport models
class MoniterModel(Document):
    UUID = StringField(max_length=255, min_length=1)
    DEVICEID = StringField(max_length=255, min_length=1)
    KEY = StringField(max_length=255, min_length=1)
    VALUE = StringField(max_length=255, min_length=1)
    TIME = DateTimeField(default=datetime.now())

class DeviceModel(Document):
    UUID = StringField(max_length=255, min_length=1)
    CPU = StringField(max_length=255, min_length=1)
    MEMORY = StringField(max_length=255, min_length=1)
    Network_Adapter = StringField(max_length=255, min_length=1)
    DISK = StringField(max_length=255, min_length=1)

class platform(Document):
    VMLIST = StringField()    
    
# factory method
# get specific metric model object from Metric object
def from_metric(met):
    ret = []
    for mdl in route.type_models[met.type]:
        obj = MetricModel()
        if globals().has_key(mdl):
            obj = globals()[mdl]()
            if met.type == "inventory":
                obj.host = met.tags["uuid"]
                obj.display_name = route.names.get(met.name, met.name)
        else:
            log.warning("unknown metric: %s", met.message_json())
        obj.name = met.name
        obj.timestamp = datetime.fromtimestamp(met.timestamp)
        obj.value = met.value
        for k, v in met.tags.iteritems():
            setattr(obj, k, v)
        ret.append(obj)  
    print ret      
    return ret
    
# get latest item for given model and metric entry
def current_item(model, met):
    tags = dict(name = met.name)
    tags.update(met.tags)
    return model.objects(**tags)

# uniform save method
# save metric to each model defined in models_route.py
def save_metric(met, debug=False):
    for mdl in from_metric(met):
        # check if only save latest value
        if route.model_conf[mdl.__class__.__name__]["latest"]:
            current_item(mdl.__class__, met).delete()
            
        # log.info(" ".join(("save ->", str(mdl.__class__), met.name, str(met.timestamp))))
        print " ".join(("save ->", mdl.__class__.__name__, met.name, str(met.timestamp)))
        if not debug: mdl.save()
    
def _test():
    model_list = [CurrentModel, CurrentInfoModel, ConfigModel, MetricModel, UserInfoModel, InventoryInfoModel, MetricInfoModel, PluginInfoModel, 
                  PluginModel, AgentModel, RuleModel, MoniterModel, DeviceModel]
                  
    for cls in model_list:
        print cls
        print "----------------------"

        rows = []
        for x in cls.objects(): 
            for r in iter(x):
                if r not in rows: rows.append(r)
        
        # csv format
        print ",".join([r for r in rows])
        for x in cls.objects():
            try:
                print ",".join(['"' + getattr(x, r, "").__str__().replace('"', '""') + '"'  for r in rows])
            except: pass

if __name__ == "__main__":_test()