from mongoengine import *
from agent_types import *
from datetime import datetime

connect("MoniterDB")

# 0. METRIC models
class BaseMetricModel(DynamicDocument):
    name = StringField(max_length=300)
    timestamp = DateTimeField()
    # tags: will be dynamically added
    
class MetricModel(DynamicDocument):
    value = FloatField()
    
class ConfigModel(DynamicDocument):
    value = StringField()

# get specific metric model object from Metric object
def from_metric(met):
    pass

# 1. STATIC INFO models

class BaseInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    # tags: will be dynamically added
    # todo: add viewmodel?

# user and group info
class UserInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
    type = StringField(max_length=200) # user or group
    inventory = ListField(UUIDField(binary=False)) # different from children(sub objects)

# InventoryModel stores entity index and info
class InventoryInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
    type = StringField(max_length=300)

# Hostinfo model
class HostInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
    address = StringField(max_length=32)

class VMInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
    address = StringField(max_length=32)
    vmid = UUIDField(binary=False)
    
class ServiceInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
class MetricInfoModel(DynamicDocument):
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
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
    uuid = UUIDField(binary=False, primary_key=True)
    name = StringField(max_length=300)
    parent = UUIDField(binary=False) # parent entity
    owner = UUIDField(binary=False) # owner(user/group)
    children = ListField(UUIDField(binary=False)) # 
    
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
    host = UUIDField(binary=False)
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