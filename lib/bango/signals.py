import django.dispatch

create = django.dispatch.Signal(providing_args=['bundle'])
