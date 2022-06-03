from organization.models import OrganizationUser
from django.utils import timezone
import datetime, validators, pytz
from django import template

register = template.Library()

@register.simple_tag(name='time_to_local')
def current_time(request, datetime_obj):
	organization_user_id = request.session['organization_user_id']
	organization_user = OrganizationUser.objects.get(
		pk=organization_user_id, 
		is_active=True, 
		deleted=False
	)
	org_timezone = organization_user.organization.timezone
	if not validators.truthy(org_timezone):
		return datetime_obj

	local_timezone = pytz.timezone(org_timezone)
	local_datetime = datetime_obj.astimezone(local_timezone)
	if local_datetime.year == timezone.now().year:
		return local_datetime.strftime('%d %b, %H:%M')
	
	return local_datetime.strftime('%d %b, %Y %H:%M')
	
