from tastypie.api import Api

from lib.bluevia.resources import PayResource


bluevia = Api(api_name='bluevia')
bluevia.register(PayResource())
