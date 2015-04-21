from rest_framework.response import Response

from lib.transactions.forms import UpdateForm
from lib.transactions.models import Transaction
from lib.transactions.serializers import TransactionSerializer
from solitude.base import NonDeleteModelViewSet


class TransactionViewSet(NonDeleteModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_fields = ('uuid', 'seller', 'provider')

    def update(self, request, *args, **kwargs):
        # Disallow PUT, but allow PATCH.
        if not kwargs.pop('partial', False):
            return Response(status=405)

        # We only allow very limited transaction changes.
        self.object = self.get_object_or_none()
        form = UpdateForm(
            request.DATA, original_data=self.object.to_dict(), request=request)
        if form.is_valid():
            return (
                super(TransactionViewSet, self)
                .update(request, *args, **kwargs)
            )

        return self.form_errors(form)
