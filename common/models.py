from mongoengine import *
from datetime import datetime
import json, time
import agent_utils
from agent_types import *
import models_displayname as display

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
    ret = None
        
    if met.type == "config":
        ret = ConfigModel()
    elif met.type == "metric":
        ret = MetricModel()
    elif met.type == "inventory":
        ret = InventoryInfoModel()
        ret.host = met.tags["uuid"]
        ret.display_name = display.names.get(met.name, met.name)
    # special type that do not save into db
    elif met.type == "current":
        return None
                
    # backport
    elif met.type == "MoniterModel":
        re_uuid = met.tags["uuid"]
        re_ts = met.timestamp
        ret = []
        for info in met.value:
            for key, value in info.iteritems():
                deviceID = key
                for k,v in value.iteritems():
                    model = MoniterModel(UUID = re_uuid, KEY = k, VALUE = json.dumps(v), TIME = datetime.fromtimestamp(re_ts), DEVICEID = deviceID)
                  #  print "save -> ", met
                    ret.append(model)
        return ret
    elif met.type == "DeviceModel":
        re_uuid = met.tags["uuid"]
        re_ts = met.timestamp
        infos = met.value
        query = DeviceModel.objects(UUID=re_uuid)
        if not query:
            ret = DeviceModel(UUID=re_uuid, CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))
          #  print "save -> ", met
            return ret
        else:
            DeviceModel.objects(UUID=re_uuid).update(CPU=json.dumps(infos['CPU']), MEMORY = json.dumps(infos['MEMORY']), DISK = json.dumps(infos['DISK']), Network_Adapter=json.dumps(infos['Network_Adapter']))
            return None
    else:
        log.warning("unknown metric: %s", met.message_json())
        ret = MetricModel()

    ret.name = met.name
    ret.timestamp = datetime.fromtimestamp(met.timestamp)
    ret.value = met.value
    for k, v in met.tags.iteritems():
        setattr(ret, k, v)
        
    return ret
    
def current_metric(met):
    ret = None
        
    if met.type in ["config", "metric", "current"]:
        ret = CurrentModel()
    elif met.type == "inventory":
        ret = CurrentInfoModel()
        ret.host = met.tags["uuid"]
        ret.display_name = display.names.get(met.name, met.name)
    else:
        log.warning("unknown metric: %s", met.message_json())
        ret = CurrentModel()

    ret.name = met.name
    ret.timestamp = datetime.fromtimestamp(met.timestamp)
    ret.value = met.value
    for k, v in met.tags.iteritems():
        setattr(ret, k, v)
    return ret
    
def current_item(model, met):
    tags = dict(name = met.name)
    tags.update(met.tags)
    return model.objects(**tags)
    
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