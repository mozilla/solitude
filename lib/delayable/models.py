import uuid

from django.db import models

from solitude.base import Model


class Delayable(Model):
    uuid = models.CharField(max_length=36)
    run = models.BooleanField(default=False)
    status_code = models.IntegerField(default=202)
    content = models.TextField()

    class Meta(Model.Meta):
        db_table = 'delayable'

    def save(self, *args, **kw):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        super(Delayable, self).save(*args, **kw)
