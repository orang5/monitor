from mongoengine import *

connect('MoniterDB')
    
class MoniterModel(Document):
    UUID = StringField(max_length=255, min_length=1)
    DEVICEID = StringField(max_length=255, min_length=1)
    KEY = StringField(max_length=255, min_length=1)
    VALUE = StringField(max_length=255, min_length=1)
    TIME = DateTimeField()

if __name__ == '__main__':
    #MoniterModel.objects.delete()
    for e in MoniterModel.objects.all():
        print e.UUID, e.DEVICEID, e.KEY, e.VALUE, e.TIME