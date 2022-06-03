from .models import Order
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Order)
def create_log(sender, instance, **kwargs):

    if instance.id is None:
        pass
    else:
        state = instance.state
        state_str = instance.DELIVERY_STATE[state-1]
        order = Order.objects.get(id=instance.id)
        order.order_status_logs.create(action=f'{state_str[1]}')