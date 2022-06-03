from rest_framework.authtoken.models import Token
from organization.models import OrganizationUser
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from api.views import TokenAPIView


class ProfileView(TokenAPIView):

	def response(self, request):
		user = request.user
		content = {
			'email' : user.email,
			'first_name' : user.first_name,
			'last_name' : user.last_name
		}
		return Response(content)

	def get(self, request, format=None):
		return self.response(request)

	def post(self, request, format=None):
		return self.response(request)

class OrganizationsView(TokenAPIView):

	def response(self, request):
		user = request.user
		orgs = []
		for org in OrganizationUser.objects.filter(user=user):
			o = org.organization
			org_name = o.name
			org_id = o.pk
			org_created = o.created.isoformat()
			orgs.append({
				'ID' : org_id,
				'name' : org_name,
				'date_created': org_created
			})
		return Response(orgs)

	def get(self, request, format=None):
		return self.response(request)

	def post(self, request, format=None):
		return self.response(request)

