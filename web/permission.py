from django.contrib.auth.models import User,Group,Permission
from django.contrib.contenttypes.models import ContentType
content_type = ContentType.objects.get_for_model(User)
try:
    permission = Permission.objects.create(codename='manage',name='manage',content_type=content_type)
except:
    pass
