import json

from django.http import HttpResponse
from django.views.decorators.http import require_POST

from .models import Buyer


@require_POST
def check_pin(request):
    data = json.loads(request.body)
    try:
        buyer = Buyer.objects.get(uuid=data['uuid'])
        result = buyer.pin.check(data['pin'])
    except Buyer.DoesNotExist:
        result = False
    return HttpResponse(json.dumps({'valid': result}))
