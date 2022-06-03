from rest_framework import authentication
from driver.models import DriverAuthToken

class CustomAuthentication(authentication.BaseAuthentication):

	def authenticate(self, request, **kwargs):
		try:
			auth_header_value = request.META.get("HTTP_AUTHORIZATION", "")
			if auth_header_value:
				authmeth, auth = request.META["HTTP_AUTHORIZATION"].split(" ", 1)
				if not auth:
					return None
				if not authmeth.lower() == "token":
					return None
				try:
					driver_auth_token = DriverAuthToken.objects.get(token=auth.strip(),is_valid=True)
					driver_auth = driver_auth_token.driver_auth
				except DriverAuth.DoesNotExist:
					return None
				return (driver_auth, auth)
			else:
				return None
		except KeyError as _e:
			return None

