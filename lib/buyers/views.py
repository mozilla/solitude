import json

from django.http import HttpResponse
from django.views.decorators.http import require_POST

from buyers.models import Buyer


@require_POST
def check_pin(request):
    data = json.loads(request.body)
    buyer = Buyer.objects.get(uuid=data['uuid'])
    response = json.dumps({'valid': buyer.pin.check(data['pin'])})
    return HttpResponse(response)
