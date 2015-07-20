from mongoengine import *

# tags can be dynamically added to this schema
class MetricModel(DynamicDocument):
    name = StringField()
    timestamp = DateTimeField()
    value = FloatField()
