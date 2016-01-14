from django.contrib.auth.models import User,Group,Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
class Perm(User):
    class Meta:
        permissions = (("manage","can manage the virtual Machine"),)
