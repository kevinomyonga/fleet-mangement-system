from order.models import Order, OrderItem, OrderFailure
from organization.models import Organization
from driver.models import Driver, DriverAuth
from order.models import Order, OrderFailure
import json, validators, base64, os
from django.utils import timezone
from datetime import datetime


def process_order( organization, order_obj, rider_obj, failures_obj, items_obj):
    prev_id_external = order_obj.pk
    order_obj = order_obj.fields
    order = Order.objects.filter(prev_id_external=prev_id_external).first()
    if order is None:
        order = Order()

    order.organization = organization
    order.prev_id_external = prev_id_external

    order.sid = order_obj.sid
    order.ref = order_obj.ref
    order.paid = order_obj.paid
    order.state = order_obj.state
    order.notes = order_obj.notes
    order.rating = order_obj.rating
    order.review = order_obj.review
    order.signature = order_obj.signature
    order.pod_images = json.loads(order_obj.pod_images) if validators.truthy(order_obj.pod_images) else order_obj.pod_images
    order.payment_method = order_obj.payment_method
    order.datetime_failed = order_obj.datetime_failed
    order.datetime_ordered = order_obj.datetime_ordered
    order.datetime_started = order_obj.datetime_started
    order.datetime_arrived = order_obj.datetime_arrived
    order.datetime_assigned = order_obj.datetime_assigned
    order.datetime_accepted = order_obj.datetime_accepted
    order.datetime_reviewed = order_obj.datetime_reviewed
    order.datetime_completed = order_obj.datetime_completed
    order.preffered_delivery_date = order_obj.preffered_delivery_date

    order.pickup_lat = order_obj.pickup_lat
    order.pickup_lng = order_obj.pickup_lng
    order.pickup_contact_name = order_obj.pickup_contact_name
    order.pickup_location_name = order_obj.pickup_location_name
    order.pickup_contact_email = order_obj.pickup_contact_email
    order.pickup_contact_phone_number = order_obj.pickup_contact_phone_number

    order.dropoff_lat = order_obj.dropoff_lat
    order.dropoff_lng = order_obj.dropoff_lng
    order.dropoff_contact_name = order_obj.dropoff_contact_name
    order.dropoff_contact_email = order_obj.dropoff_contact_email
    order.dropoff_location_name = order_obj.dropoff_location_name
    order.dropoff_contact_phone_number = order_obj.dropoff_contact_phone_number

    order.added_by = organization.owner
    order.modified_by = organization.owner

    rider = None
    if validators.truthy(rider_obj):
        prev_id_external = rider_obj.pk
        rider_obj = rider_obj.fields
        phone_number = rider_obj.phone_number
        rider = Driver.objects.get_by_phone_number(phone_number,organization)
        created = rider_obj.created
        modified = rider_obj.modified

        if rider is not None:
            Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
            rider = Driver.objects.get(pk=rider.pk)
        else:
            first_name = rider_obj.first_name
            last_name = rider_obj.last_name
            name = '{} {}'.format(first_name if validators.truthy(first_name) else "", last_name if validators.truthy(last_name) else "")

            rider = Driver.objects.create_new(phone_number, organization, name, rider_obj.reg_no)
            Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
            rider = Driver.objects.get(pk=rider.pk)

    order.rider = rider
    order.save()

    if validators.truthy(failures_obj):
        order.failures.clear()
        for failure_obj in failures_obj:
            of = OrderFailure()
            failure_obj = failure_obj.fields
            created = failure_obj.created
            of.reason = failure_obj.reason
            of.save()
            OrderFailure.objects.filter(pk=of.pk).update(created=created)
            order.failures.add(OrderFailure.objects.get(pk=of.pk))


    if validators.truthy(items_obj):
        order.items.clear()
        for item_obj in items_obj:
            item = OrderItem()
            item_obj = item_obj.fields
            item.paid = item_obj.paid
            item.name = item_obj.name
            item.state = item_obj.state
            item.price = item_obj.price
            item.width = item_obj.width
            item.weight = item_obj.weight
            item.length = item_obj.length
            item.height = item_obj.height
            item.save()
            order.items.add(item)
    order.save()

    public_id = base64.b64encode(bytes(str(order.pk), 'ascii')).decode().strip("=")
    Order.objects.filter(pk=order.pk).update(created=order_obj.created, modified=order_obj.modified, public_id=public_id)
    return Order.objects.get(pk=order.pk)
