from collections import defaultdict

from rest_framework.exceptions import ParseError


class ErrorFormatter(object):

    def __init__(self, error):
        self.error = error


class MozillaFormatter(ErrorFormatter):

    def format(self):
        errors = defaultdict(list)
        for k, error in self.error.detail.as_data().items():
            for v in error:
                errors[k].append({
                    'code': v.code,
                    'message': unicode(v.message)
                })
        return {'mozilla': dict(errors)}


class FormError(ParseError):
    status_code = 422
    default_detail = 'Error parsing form.'
    formatter = MozillaFormatter


class InvalidQueryParams(ParseError):
    status_code = 400
    default_detail = 'Incorrect query parameters.'
