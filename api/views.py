from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import  TokenAuthentication
from rest_framework.response import Response
from rest_framework import views

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from driver.models import DriverAuthToken, DriverAuth
from django.views.generic import View
from django.http import HttpResponse
import json

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

@method_decorator(csrf_exempt, name='dispatch')
class APIView(View):
	jsn = None
	driver = None
	def __init__(self):
		self.status = 400
		self.payload = {}

	def handle_params(self):
		try:
			self.jsn = json.loads(self.request.body)
		except (NameError, json.JSONDecodeError) as e:
			pass

	def get_param(self, param_name):
		if self.jsn is None:
			self.handle_params()

		try:
			value = self.jsn[param_name]
		except (TypeError, NameError, KeyError, ValueError, json.JSONDecodeError) as e:
			value = None

		return value

	def send_response(self, results):
		self.status = 200
		self.payload = results
		return self.push_payload()

	def send_error(self, error):
		self.status = 400
		self.payload['error'] = error
		return self.push_payload()

	def push_payload(self):
		response = JsonResponse(
			self.request,
			self.payload,
			status=self.status
		)
		return response


	def get_driver_auth(self):
		try:
			auth_header_value = self.request.META.get("HTTP_AUTHORIZATION", "")
			if auth_header_value:
				authmeth, auth = self.request.META["HTTP_AUTHORIZATION"].split(" ", 1)
				if not auth:
					return None
				if not authmeth.lower() == "token":
					return None
				try:
					driver_auth_token = DriverAuthToken.objects.get(token=auth.strip())
				except DriverAuthToken.DoesNotExist:
					return None
				return driver_auth_token.driver_auth
			else:
				return None
		except KeyError as _e:
			return None


class TokenAPIView(views.APIView):
	authentication_classes = [TokenAuthentication]
	permission_classes = [IsAuthenticated]
	jsn = None

	def handle_params(self):
		try:
			self.jsn = json.loads(self.request.body)
		except (NameError, json.JSONDecodeError) as e:
			pass

	def get_param(self, param_name):
		if self.jsn is None:
			return None

		try:
			value = self.jsn[param_name]
		except (NameError, KeyError, ValueError, json.JSONDecodeError) as e:
			value = None

		return value
