'''

import pytest
from order.signals import create_log
from order.models import Order, OrderStatusLog
from organization.models import Organization
from user.models import User

from django.utils import timezone



from mixer.backend.django import mixer


@pytest.mark.django_db
# @patch('order.signals.create_log')
def test_should_call_create_log_when_order_changed():
    user = User.objects.create(email="test@test.com", first_name="Test", is_active=True, is_email_verified=True, last_name="Doe", password="test@1234")
    organization = Organization.objects.create(owner=user, name="stickman", is_active=True)
    order = Order.objects.create(created=timezone.now(), organization=organization, public_id=1, state=1, ref=1, paid=True)
    # order = Order.objects.create(organization=organization, public_id="Test Order")
    log = OrderStatusLog.objects.create(order_id=order)

    assert(order.order_status_logs is not None)
    assert(log.order_id.pk == order.pk)
    assert(log.action != None)
    assert(log.created_at != "" and log.created_at is not None)


'''
