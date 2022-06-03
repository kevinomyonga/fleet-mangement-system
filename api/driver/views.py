from driver.models import Driver, DriverAuth, DriverAuthFCM, DriverAuthToken
from django.contrib.auth import authenticate
from sms.tasks import send_verify_message
import validators, secrets, random
from django.utils import timezone
from firebase_admin import auth
from api.views import APIView
from organization.models import OrganizationMpesaDetails


def organizations_json(driver):

    orgz = []
    for driver in Driver.objects.filter(phone_number=driver.phone_number):
        org = driver.organization
        org_name = org.name
        org_id = org.pk
        org_is_active = org.is_active
        org_mpesa_details = OrganizationMpesaDetails.objects.filter(
            organization=org).exists()
        orgz.append({
            'ID': org_id,
            'name': org_name,
            'isActive': org_is_active,
            'hasSTKPush': org_mpesa_details
        })

    return orgz


def driver_user_json(driver):
    if driver is None:
        return {}

    return {
        'last_name': driver.last_name,
        'first_name': driver.first_name,
        'phone_number': driver.phone_number,
        'date_created': driver.created.isoformat(),
        'date_modified': driver.modified.isoformat(),
        'thumbnail': driver.thumbnail,
        'avatar': driver.avatar,
        'organizations': organizations_json(driver)
    }


def driver_auth_json(driver_auth):
    if driver_auth is None:
        return {}

    frb_token = auth.create_custom_token(
        str(driver_auth.phone_number)).decode('UTF-8')
    # TODO: Invalidate all token
    token = secrets.token_hex(32)

    driver_auth_token = DriverAuthToken.objects.create(
        driver_auth=driver_auth, token=token)
    tokens = {
        'firebase_token': frb_token,
        'server_token': driver_auth_token.token,
        'isPasswordSet': driver_auth.is_password
    }
    return {'tokens': tokens, 'user': driver_user_json(driver_auth)}


class AuthView(APIView):

    def post(self, request, format=None):
        self.handle_params()
        password = self.get_param("password")
        phone_number = self.get_param("phone_number")

        phone_number = self.get_param("phone_number")
        if not validators.truthy(phone_number):
            return self.send_error('Invalid phone number')

        try:
            phone_number = int(phone_number)
        except ValueError:
            return self.send_error('Invalid phone number')

        if not validators.between(phone_number, 100000000, 999999999999):
            return self.send_error('Invalid phone number')

        password = self.get_param("password")
        if not validators.truthy(password) or len(password.strip()) < 6:
            return self.send_error('Invalid password')

        driver_auth = DriverAuth.objects.auth(phone_number, password)
        if driver_auth is None:
            return self.send_error('Invalid password/phone number combination')

        return self.send_response(driver_auth_json(driver_auth))


class ProfileUpdateView(APIView):

    def post(self, request, format=None):
        driver_auth = self.get_driver_auth()
        if driver_auth is None:
            return self.send_error('Invalid authentication')

        self.handle_params()
        last_name = self.get_param("last_name")
        if validators.truthy(last_name):
            driver_auth.last_name = last_name.strip()
            driver_auth.save()

        first_name = self.get_param("first_name")
        if validators.truthy(first_name):
            driver_auth.first_name = first_name.strip()
            driver_auth.save()

        thumbnail = self.get_param("thumbnail")
        if validators.truthy(thumbnail) and validators.url(thumbnail):
            driver_auth.thumbnail = thumbnail.strip()
            driver_auth.save()

        avatar = self.get_param("avatar")
        if validators.truthy(avatar) and validators.url(avatar):
            driver_auth.avatar = avatar.strip()
            driver_auth.save()

        driver_auth.refresh_from_db()
        return self.send_response(driver_user_json(driver_auth))


class ProfileView(APIView):

    def do_response(self):
        driver_auth = self.get_driver_auth()
        if driver_auth is None:
            return self.send_error('Invalid authentication')

        return self.send_response(driver_user_json(driver_auth))

    def get(self, request):
        return self.do_response()

    def post(self, request):
        return self.do_response()


class PasswordSetView(APIView):

    def post(self, request):
        driver_auth = self.get_driver_auth()
        if driver_auth is None:
            return self.send_error('Invalid authentication')

        self.handle_params()
        password = self.get_param("password")
        confirm_password = self.get_param("confirm_password")

        if not validators.truthy(password) or not validators.truthy(confirm_password):
            return self.send_error('Invalid password')

        password = password.strip()
        confirm_password = confirm_password.strip()
        if password != confirm_password or len(password) < 6:
            return self.send_error('Invalid password')

        driver_auth.set_password(password)
        driver_auth.is_password = True
        driver_auth.save()
        return self.send_response(driver_auth_json(driver_auth))


class PhoneVerifyView(APIView):

    def post(self, request, format=None):
        self.handle_params()
        code = self.get_param("code")
        phone_number = self.get_param("phone_number")
        if not validators.truthy(phone_number):
            return self.send_error('Invalid phone number')

        if not validators.truthy(code):
            return self.send_error('Invalid code')

        try:
            phone_number = int(phone_number)
        except ValueError:
            return self.send_error('Invalid phone number')

        try:
            code = int(code)
        except ValueError:
            return self.send_error('Invalid code')

        if not validators.between(phone_number, 100000000, 999999999999):
            return self.send_error('Invalid phone number')

        if not validators.between(code, 111111, 999999):
            return self.send_error('Invalid code')

        try:
            driver_auth = DriverAuth.objects.get(
                phone_number=phone_number, verification_code=code)
            driver_auth.verification_tries = driver_auth.verification_tries + 1
            driver_auth.save()
        except DriverAuth.DoesNotExist:
            return self.send_error('Invalid code')

        if driver_auth.verification_tries > 10:
            return self.send_error('Invalid code')

        #time_spent = timezone.now() - driver_auth.verification_time
        # if time_spent.seconds > 900:
        #	return self.send_error('Invalid code')

        return self.send_response(driver_auth_json(driver_auth))


class PhoneCodeView(APIView):

    def post(self, request, format=None):
        phone_number = self.get_param("phone_number")
        if not validators.truthy(phone_number):
            return self.send_error('Invalid phone number')

        try:
            phone_number = int(phone_number)
        except ValueError:
            return self.send_error('Invalid phone number')

        if not validators.between(phone_number, 100000000, 999999999999):
            return self.send_error('Invalid phone number')

        driver = DriverAuth.objects.get_by_phone_number(phone_number)
        if driver is None:
            driver = DriverAuth.objects.create_new(
                phone_number, secrets.token_hex(6))

        time_diff = timezone.now() - driver.verification_time
        time_diff_seconds = int(time_diff.total_seconds())
        send_count = driver.code_send_count
        wait_time = 0
        if time_diff_seconds < 60:
            if send_count < 1:
                wait_time = 0
            else:
                wait_time = 60 - time_diff_seconds

        elif time_diff_seconds < 300:
            if send_count < 2:
                wait_time = 0
            else:
                wait_time = 300 - time_diff_seconds

        elif time_diff_seconds < 600:
            if send_count < 3:
                wait_time = 0
            else:
                wait_time = 600 - time_diff_seconds

        elif time_diff_seconds < 1800:
            if send_count < 4:
                wait_time = 0
            else:
                wait_time = 1800 - time_diff_seconds

        elif time_diff_seconds < 3600:
            if send_count < 5:
                wait_time = 0
            else:
                wait_time = 3600 - time_diff_seconds

        elif time_diff_seconds < 7200:
            if send_count < 6:
                wait_time = 0
            else:
                wait_time = 7200 - time_diff_seconds

        elif time_diff_seconds < 86400:
            if send_count < 7:
                wait_time = 0
            else:
                wait_time = 86400 - time_diff_seconds
        elif time_diff_seconds > 86400:
            driver.code_send_count = 0

        message = f'Verification code not sent, wait {wait_time} seconds before you try again'
        if wait_time == 0:
            driver.verification_code = random.randint(111111, 999999)
            driver.verification_time = timezone.now()
            driver.verification_tries = 0
            driver.code_send_count = driver.code_send_count + 1
            driver.save()

            msg_res = send_verify_message(
                driver.verification_code, phone_number)
            wait_time = 60
            message = 'Verification code sent'

        content = {'message': message, 'wait_time': wait_time}
        return self.send_response(content)

        content = {'message': message, 'wait_time': wait_time}
        return self.send_response(content)


class LocationView(APIView):
    def get(self, request, format=None):
        return self.send_error('Method not allowed')

    def post(self, request, format=None):
        driver_auth = self.get_driver_auth()
        if driver_auth is None:
            return self.send_error('Invalid authentication')

        lat = self.get_param("lat")
        lng = self.get_param("lng")

        if not validators.truthy(lat) or not validators.truthy(lng):
            return self.send_error('Invalid params')

        driver_auth.location_update_time = timezone.now()
        driver_auth.lat = lat
        driver_auth.lng = lng
        driver_auth.save()

        return self.send_response(driver_user_json(driver_auth))


class FCMUpdateView(APIView):
    def get(self, request, format=None):
        return self.send_error('Method not allowed')

    def post(self, request, format=None):
        driver_auth = self.get_driver_auth()
        if driver_auth is None:
            return self.send_error('Invalid authentication')

        token = self.get_param("token")
        if not validators.truthy(token):
            return self.send_error('Invalid token')

        token = token.strip()
        driver_auth_fcm, created = DriverAuthFCM.objects.get_or_create(
            token=token, driver_auth=driver_auth)
        driver_auth_fcm.is_valid = True
        driver_auth_fcm.last_fail_time = None
        driver_auth_fcm.failed_tries = 0
        driver_auth_fcm.save()
        return self.send_response(driver_user_json(driver_auth))
