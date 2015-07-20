from mongoengine import *

connect("MoniterDB")

# tags can be dynamically added to this schema
class MetricModel(DynamicDocument):
    name = StringField()
    timestamp = DateTimeField()
    value = FloatField()
