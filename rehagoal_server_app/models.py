from __future__ import unicode_literals

import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from typing import Optional, Any
from private_storage.fields import PrivateFileField


ID_LENGTH = 12
FILENAME_STRING_CHARS = string.ascii_letters + string.digits
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MiB


def pkgen():
    return get_random_string(length=ID_LENGTH)


def replace_filename(_instance, _filename):
    return get_random_string(length=ID_LENGTH, allowed_chars=FILENAME_STRING_CHARS)


class RehagoalUser(models.Model):
    id = models.SlugField(max_length=ID_LENGTH, primary_key=True, default=pkgen)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rehagoal_user')

    def __str__(self):
        return "%s (%s)" % (self.user.username, self.id)


# proxy for simple admin interface
class SimpleUser(User):
    class Meta:
        proxy = True
        verbose_name = "BenutzerIn"
        verbose_name_plural = "BenutzerInnen"


def create_rehagoal_user(sender, **kwargs):
    user = kwargs["instance"]
    if kwargs["created"]:
        rehagoal_user = RehagoalUser(user=user)
        rehagoal_user.save()


post_save.connect(create_rehagoal_user, sender=User)
post_save.connect(create_rehagoal_user, sender=SimpleUser)


class Workflow(models.Model):
    id = models.SlugField(max_length=ID_LENGTH, primary_key=True, default=pkgen)
    owner = models.ForeignKey(RehagoalUser, on_delete=models.CASCADE)
    content = PrivateFileField(upload_to=replace_filename, max_file_size=MAX_FILE_SIZE)

    def __str__(self):
        return "%s by %s" % (self.id, self.owner.user.username)

    def delete_content(self, save=True):
        if self.content:
            self.content.delete(save=save)

    class Meta:
        ordering = ['id']


@receiver(post_delete, sender=Workflow)
def auto_delete_content_file_on_post_delete(instance, **_kwargs):
    # Do not save, to prevent model from being persisted again to DB
    instance.delete_content(save=False)


@receiver(pre_save, sender=Workflow)
def auto_delete_content_file_on_pre_save(instance: Workflow, raw: bool, using: str, update_fields: Optional[Any], **_kwargs):
    try:
        # Get old instance (if exists), as new instance already has new filename
        old_instance = Workflow.objects.get(id=instance.id)
        # Check that instance content has actually changed, to prevent false deletion (e.g. partial update)
        if instance.content != old_instance.content:
            # Do not save, to prevent infinite recursion (FileField.delete calls .save)
            old_instance.delete_content(save=False)
    except Workflow.DoesNotExist:  # to handle initial object creation
        return
