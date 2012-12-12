from django.db import models
from django.test import RequestFactory
from django.utils import importlib

from celery.task import task


@task
def delayable(module, name, request_type, meta, body, kw, uuid):
    model = models.get_model('delayable', 'Delayable')
    module = importlib.import_module(module)
    dispatch = getattr(module, name)().dispatch
    method = getattr(RequestFactory(), meta.pop('REQUEST_METHOD').lower())
    request = method(meta.pop('PATH_INFO'), content_type='application/json',
                     data=body, **meta)

    obj, created = model.objects.get_or_create(uuid=uuid)
    try:
        response = dispatch(request_type, request, **kw)
        # TODO: check that 500's here get reported correctly, I suspect celery
        # does something sneaky.
    finally:
        obj.run = True
        obj.save()

    obj.run = True
    obj.status_code = response.status_code
    obj.content = response.content
    obj.save()
    # Primarily for testing.
    return obj
