from django.views.generic import View
from django.http import HttpResponse
from . import models

class PermissionView(View):

	def get_current_organization(self):
		organization_user_id = self.request.session['organization_user_id']
		organization_user = models.OrganizationUser.objects.get(
			pk=organization_user_id, 
			is_active=True, 
			deleted=False
		)
		return organization_user.organization

	def get_map_key(self):
		organization_user_id = self.request.session['organization_user_id']
		organization_user = models.OrganizationUser.objects.get(
			pk=organization_user_id, 
			is_active=True, 
			deleted=False
		)
		return organization_user.organization.googlemap_api_key
