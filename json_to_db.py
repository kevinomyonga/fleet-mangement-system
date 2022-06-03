import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PROJECT.settings")

import django
django.setup()

from django.core.management import call_command

from django.contrib.contenttypes.models import ContentType
from organization.models import Organization
from driver.models import Driver, DriverAuth
from django.core import serializers
from django.utils import timezone
from order.models import Order, OrderFailure
from datetime import datetime
import json, validators, base64

path = '/home/qwertie/PythonProjects/AndrewProjects/business/data-dump/db-json'
shippings_folder = 'ocation.models.ShippingLocation'
contacts_folder = 'orders.models.OrderCustomer'
failures_folder = 'orders.models.OrderFailure'
orders_folder = 'orders.models.Order'
riders_folder = 'fleet.models.Driver'
users_folder = 'users.models.User'


org = Organization.objects.get(pk=1)
owner = org.owner


def str_to_date(date_string):
    if validators.truthy(date_string):
        try:
            return timezone.make_aware(datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ'))
        except ValueError:
            return timezone.make_aware(datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ'))

    return None

def get_faliure(failure_id):
    if not validators.truthy(failure_id):
        return none

    failure_json = json.load(open(f"{path}/{failures_folder}/{failure_id}.json"))
    of = OrderFailure()
    created = str_to_date(failure_json.get("fields").get("created"))
    of.reason = failure_json.get("fields").get("reason")
    of.save()
    OrderFailure.objects.filter(pk=of.pk).update(created=created)
    return OrderFailure.objects.get(pk=of.pk)

def get_rider(rider_id):
    if not validators.truthy(rider_id):
        return None

    rider_json = json.load(open(f"{path}/{riders_folder}/{rider_id}.json"))
    prev_id_external = rider_json.get("pk")
    phone_number = rider_json.get("fields").get("phone_number")
    rider = Driver.objects.get_by_phone_number(phone_number)
    created = str_to_date(rider_json.get("fields").get("created_date"))
    modified = str_to_date(rider_json.get("fields").get("updated_date"))
    if rider is not None:
        Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
        return Driver.objects.get(pk=rider.pk)

    driver_auth = DriverAuth.objects.get_by_phone_number(phone_number)
    if driver_auth is None:
        driver_auth = DriverAuth.objects.create_new(phone_number, str(phone_number))

    user_id = rider_json.get("fields").get("user")
    user_json = json.load(open(f"{path}/{users_folder}/{user_id}.json"))

    first_name = user_json.get("fields").get("first_name")
    last_name = user_json.get("fields").get("last_name")
    name = '{} {}'.format(first_name if validators.truthy(first_name) else "", last_name if validators.truthy(last_name) else "")
    rider = Driver.objects.create_new(phone_number, org, name, None)
    Driver.objects.filter(pk=rider.pk).update(created=created,modified=modified,prev_id_external=prev_id_external)
    return Driver.objects.get(pk=rider.pk)



def get_dropoff_details(shipping_id, customer_id):
    customer_name = None
    customer_phone_number = None
    customer_email = None
    location_name = None
    lat = None
    lng = None
    print(shipping_id)
    if validators.truthy(shipping_id):
        shipping = json.load(open(f"{path}/{shippings_folder}/{shipping_id}.json"))
        location_name = shipping.get("fields").get("location_name")
        lat = shipping.get("fields").get("lat")
        lng = shipping.get("fields").get("lng")

    if validators.truthy(customer_id):
        contact = json.load(open(f"{path}/{contacts_folder}/{customer_id}.json"))
        first_name = contact.get("fields").get("first_name")
        last_name = contact.get("fields").get("last_name")
        customer_phone_number = contact.get("fields").get("phone_number")
        try:
            customer_phone_number = int(customer_phone_number)
            if not validators.between(customer_phone_number, 100000000, 99999999999999):
                customer_phone_number = None
        except ValueError as e:
            customer_phone_number = None
            print(e)

        customer_email = contact.get("fields").get("email")
        customer_name = '{} {}'.format(first_name if validators.truthy(first_name) else "", last_name if validators.truthy(last_name) else "")

    return (customer_name, customer_phone_number, customer_email, location_name, lat, lng)

def get_pod_images(pod1, pod2):
    images = []
    if validators.truthy(pod1) and validators.url(pod1):
        images.append(pod1)
    if validators.truthy(pod2):
        for pod in pod2:
            if validators.truthy(pod) and validators.url(pod):
                images.append(pod)
    return images if len(images) > 0 else None

def process_order(j, prev_id_external):
    created = str_to_date(j.get("created_date"))
    modified = str_to_date(j.get("updated_date"))
    print(prev_id_external)
    order = Order.objects.filter(prev_id_external=prev_id_external).first()
    if order is None:
        order = Order()

    order.prev_id_external = prev_id_external
    rating = j.get("rating") if float(j.get("rating")) > 0 else None
    order.rating = rating
    order.review = j.get("comments")
    order.organization = org
    order.paid = True
    order.sid = j.get("order_no")
    order.ref = j.get("order_ref")
    order.payment_method = 1
    order.state = j.get("state")
    order.notes = j.get("order_instructions")
    date_ordered = str_to_date(j.get("order_datetime"))
    order.datetime_ordered = date_ordered if date_ordered is not None else created
    order.datetime_assigned = str_to_date(j.get("assigned_datetime"))
    order.datetime_accepted = str_to_date(j.get("accepted_datetime"))
    order.datetime_started = str_to_date(j.get("started_datetime"))
    order.datetime_arrived = str_to_date(j.get("arrived_datetime"))
    order.datetime_failed = str_to_date(j.get("failed_datetime"))
    order.datetime_completed = str_to_date(j.get("completed_datetime"))
    if order.rating is not None:
        order.datetime_reviewed = order.datetime_completed
    order.signature = j.get("signature")
    order.pod_images = get_pod_images(j.get("pod_image_1"), j.get("pod_images"))

    order.pickup_location_name = "MyDawa HQ"
    order.pickup_contact_phone_number = 254205219999
    order.pickup_contact_name = "MyDawa"
    order.pickup_contact_email = "support@mydawa.com"
    order.pickup_lat = -1.254766
    order.pickup_lng = 36.797427

    customer_name, customer_phone_number, customer_email, location_name, lat, lng = get_dropoff_details(j.get("shipping_location"), j.get("order_customer"))


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

    order.added_by = owner
    order.modified_by = owner
    order.preffered_delivery_date = order.datetime_ordered

    order.rider = get_rider(j.get("rider"))
    order.save()

    for failure_id in j.get("failures"):
        order.failures.add(get_faliure(failure_id))
    order.save()

    public_id = base64.b64encode(bytes(str(order.pk), 'ascii')).decode().strip("=")
    Order.objects.filter(pk=order.pk).update(created=created, modified=modified, public_id=public_id)
    print(order.pk)


if __name__ == "__main__":
    file_paths = os.listdir(f"{path}/{orders_folder}")
    for file_path in file_paths:
        j = json.load(open(f"{path}/{orders_folder}/{file_path}"))
        prev_id_external = j.get("pk")
        j = j.get("fields")
        process_order(j, prev_id_external)
