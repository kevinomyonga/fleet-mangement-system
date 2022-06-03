from organization.models import OrganizationUser
from django.conf import settings
from django import template
register = template.Library()

@register.inclusion_tag('organization/tags/display_organizations.html')
def display_organizations(request):
	organization_user_id = request.session['organization_user_id']
	organization_user = OrganizationUser.objects.get(
		pk=organization_user_id, 
		is_active=True, 
		deleted=False
	)
	organization_users = OrganizationUser.objects.filter(
			user__email=request.user.email, 
			is_active=True, 
			deleted=False
	).exclude(pk=organization_user_id).order_by('-modified')

	
	ws_connect_url = f'{settings.WS_CONNECT_URL}/{organization_user.organization.pk}/{organization_user.user.pk}'
	return {
		'current_user' : request.user,
		'organization_user' : organization_user,
		'organization_users' : organization_users,
		'ws_connect_url' : ws_connect_url
	}
