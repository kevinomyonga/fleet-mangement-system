import decimal
import simplejson
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers

class DecimalEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def dumps(*args, **kwargs):
    return simplejson.dumps(
        *args,
        sort_keys=True,
        separators=(',', ': '),
        indent=4,
        use_decimal=False,
        cls=DecimalEncoder,
        **kwargs
    )

def loads(*args, **kwargs):
    return simplejson.loads(*args, **kwargs)

class JsonResponse(HttpResponse):
    def __init__(self, request, content, **kwargs):
        data = dumps(content)
        try:
            if "application/json" in request.META['HTTP_ACCEPT_ENCODING']:
                mimetype = 'application/json'
            else:
                raise KeyError('application/json not accepted')
        except:
            mimetype = 'text/plain'
        super(JsonResponse, self).__init__(data, mimetype, **kwargs)
        add_never_cache_headers(self)