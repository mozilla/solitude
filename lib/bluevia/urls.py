from tastypie.api import Api

from lib.bluevia.resources import PayResource, VerifyResource


bluevia = Api(api_name='bluevia')
bluevia.register(PayResource())
bluevia.register(VerifyResource())
