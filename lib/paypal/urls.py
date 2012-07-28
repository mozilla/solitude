from tastypie.api import Api

from lib.paypal.resources.check import AccountCheckResource
from lib.paypal.resources.ipn import IPNResource
from lib.paypal.resources.permission import (CheckPermissionResource,
                                             GetPermissionTokenResource,
                                             GetPermissionURLResource)
from lib.paypal.resources.personal import (CheckPersonalBasic,
                                           CheckPersonalAdvanced)
from lib.paypal.resources.preapproval import PreapprovalResource
from lib.paypal.resources.pay import (CheckPurchaseResource, PayResource,
                                      RefundResource)

paypal = Api(api_name='paypal')
paypal.register(CheckPurchaseResource())
paypal.register(PayResource())
paypal.register(IPNResource())
paypal.register(PreapprovalResource())
paypal.register(GetPermissionURLResource())
paypal.register(CheckPermissionResource())
paypal.register(GetPermissionTokenResource())
paypal.register(CheckPersonalBasic())
paypal.register(CheckPersonalAdvanced())
paypal.register(RefundResource())
paypal.register(AccountCheckResource())
