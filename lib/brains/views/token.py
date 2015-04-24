from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.brains.client import get_client


@api_view(['POST'])
def generate(request):
    return Response({'token': get_client().ClientToken.generate()})
