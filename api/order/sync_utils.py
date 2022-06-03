from organization.models import Organization
from driver.models import Driver, DriverAuth
from order.models import Order, OrderFailure
import json, validators, base64, os
from django.core import serializers
from django.utils import timezone
from datetime import datetime

def str_to_date(date_string):
    if validators.truthy(date_string):
        try:
            return timezone.make_aware(datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ'))
        except ValueError:
            return timezone.make_aware(datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ'))

    return None

def get_pod_images(pod1, pod2):
    images = []
    if validators.truthy(pod1) and validators.url(pod1):
        images.append(pod1)
    if validators.truthy(pod2):
        for pod in pod2:
            if validators.truthy(pod) and validators.url(pod):
                images.append(pod)
    return images if len(images) > 0 else None

def process_order(
    organization, order_json, shipping_json,
    customer_json, rider_json, user_json, faliures_json
    ):
    prev_id_external = order_json.get("pk")
    order_json = order_json.get("fields")
    created = str_to_date(order_json.get("created_date"))
    modified = str_to_date(order_json.get("updated_date"))
    print(prev_id_external)
    order = Order.objects.filter(prev_id_external=prev_id_external).first()
    if order is None:
        order = Order()

    order.prev_id_external = prev_id_external
    rating = order_json.get("rating") if float(order_json.get("rating")) > 0 else None
    order.rating = rating
    order.review = order_json.get("comments")
    order.organization = organization
    order.paid = True
    order.sid = order_json.get("order_no")
    order.ref = order_json.get("order_ref")
    order.payment_method = 1
    order.state = order_json.get("state")
    order.notes = order_json.get("order_instructions")
    date_ordered = str_to_date(order_json.get("order_datetime"))
    order.datetime_ordered = date_ordered if date_ordered is not None else created
    order.datetime_assigned = str_to_date(order_json.get("assigned_datetime"))
    order.datetime_accepted = str_to_date(order_json.get("accepted_datetime"))
    order.datetime_started = str_to_date(order_json.get("started_datetime"))
    order.datetime_arrived = str_to_date(order_json.get("arrived_datetime"))
    order.datetime_failed = str_to_date(order_json.get("failed_datetime"))
    order.datetime_completed = str_to_date(order_json.get("completed_datetime"))

    if order.rating is not None:
        order.datetime_reviewed = order.datetime_completed

    order.signature = order_json.get("signature")
    order.pod_images = get_pod_images(order_json.get("pod_image_1"), order_json.get("pod_images"))

    order.pickup_location_name = "MyDawa HQ"
    order.pickup_contact_phone_number = 254205219999
    order.pickup_contact_name = "MyDawa"
    order.pickup_contact_email = "support@mydawa.com"
    order.pickup_lat = -1.254766
    order.pickup_lng = 36.797427

    customer_name = None
    customer_phone_number = None
    customer_email = None
    location_name = None
    lat = None
    lng = None
    if validators.truthy(shipping_json):
        location_name = shipping_json.get("fields").get("location_name")
        lat = shipping_json.get("fields").get("lat")
        lng = shipping_json.get("fields").get("lng")

    if validators.truthy(customer_json):
        first_name = customer_json.get("fields").get("first_name")
        last_name = customer_json.get("fields").get("last_name")
        customer_phone_number = customer_json.get("fields").get("phone_number")
        try:
            customer_phone_number = int(customer_phone_number)
            if not validators.between(customer_phone_number, 100000000, 99999999999999):
                customer_phone_number = None
        except ValueError as e:
            customer_phone_number = None
            print(e)

        customer_email = customer_json.get("fields").get("email")
        customer_name = '{} {}'.format(first_name if validators.truthy(first_name) else "", last_name if validators.truthy(last_name) else "")


    order.dropoff_location_name = location_name
    if validators.truthy(customer_phone_number):
        try:
            customer_phone_number = int(customer_phone_number)
            order.dropoff_contact_phone_number = customer_phone_number
        except ValueError as e:
            print(e)

    order.dropoff_contact_name = customer_name
    order.dropoff_contact_email = customer_email
    order.dropoff_lat = lat
    order.dropoff_lng = lng

    order.added_by = organization.owner
    order.modified_by = organization.owner
    order.preffered_delivery_date = order.datetime_ordered


    rider = None
    if validators.truthy(rider_json) and validators.truthy(user_json):
        prev_id_external = rider_json.get("pk")
        phone_number = rider_json.get("fields").get("phone_number")
        rider = Driver.objects.get_by_phone_number(phone_number,organization)
        created = str_to_date(rider_json.get("fields").get("created_date"))
        modified = str_to_date(rider_json.get("fields").get("updated_date"))

        if rider is not None:
            Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
            rider = Driver.objects.get(pk=rider.pk)
        else:
            first_name = user_json.get("fields").get("first_name")
            last_name = user_json.get("fields").get("last_name")
            name = '{} {}'.format(first_name if validators.truthy(first_name) else "", last_name if validators.truthy(last_name) else "")
            rider = Driver.objects.create_new(phone_number, organization, name, None)
            Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
            rider = Driver.objects.get(pk=rider.pk)

    order.rider = rider
    order.save()

    if validators.truthy(faliures_json):
        order.failures.clear()
        for faliure_json in faliures_json:
            of = OrderFailure()
            created = str_to_date(faliure_json.get("fields").get("created"))
            of.reason = faliure_json.get("fields").get("reason")
            of.save()
            OrderFailure.objects.filter(pk=of.pk).update(created=created)
            order.failures.add(OrderFailure.objects.get(pk=of.pk))
    order.save()

    created = str_to_date(order_json.get("created_date"))
    modified = str_to_date(order_json.get("updated_date"))
    public_id = base64.b64encode(bytes(str(order.pk), 'ascii')).decode().strip("=")
    Order.objects.filter(pk=order.pk).update(created=created, modified=modified, public_id=public_id)
    return Order.objects.get(pk=order.pk)
