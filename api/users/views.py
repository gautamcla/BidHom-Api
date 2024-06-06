# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.packages.oauth import *
from api.packages.mail_service import send_email, compose_email, send_custom_email
from api.packages.globalfunction import *
from api.packages.common import *
from api.users.models import *
from api.bid.models import *
from api.notifications.models import *
from api.users.serializers import *
from api.advertisement.serializers import *
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
import datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum, Func, F
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models.functions import Concat, TruncDay
from django.db.models import Value as V
from django.db.models import Max, Min
from geopy.geocoders import Nominatim
from rest_framework.permissions import AllowAny
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models.functions import Now
from datetime import date


class UserRegistrationApiView(APIView):
    """
    User Registration
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    # @transaction.atomic
    @staticmethod
    def post(request):
        try:
            data = request.data
            user_type_name = 'Buyer/Seller'
            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            register_site = None
            if "register_site" in data and data['register_site'] != "":
                register_site = int(data['register_site'])
                network = NetworkDomain.objects.filter(id=register_site, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Registered site not exist.", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                users = Users.objects.filter(phone_no=phone_no).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if phone_no:
                hashed_pwd = make_password(str(phone_no))
                data['password'] = hashed_pwd
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            data['encrypted_password'] = b64encode(str(phone_no))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            # -------------Check Data for Agent/Broker Only----------------
            if user_type == 2:
                user_type_name = 'Agent/Broker'
                business_data = {}
                if "business_first_name" in data and data['business_first_name'] != "":
                    business_data['first_name'] = data['business_first_name']
                else:
                    return Response(response.parsejson("business_first_name is required", "", status=403))

                if "business_last_name" in data and data['business_last_name'] != "":
                    business_data['last_name'] = data['business_last_name']
                else:
                    return Response(response.parsejson("business_last_name is required", "", status=403))

                if "company_name" in data and data['company_name'] != "":
                    company_name = data['company_name']
                    business_data['company_name'] = data['company_name']
                else:
                    return Response(response.parsejson("company_name is required", "", status=403))

                if "business_phone_no" in data and data['business_phone_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(phone_no=data['business_phone_no']).first()
                    if user_business_profile:
                        # Translators: This message appears when phone no already in db
                        return Response(response.parsejson("Business Phone no already exist", "", status=403))
                    business_data['phone_no'] = data['business_phone_no']
                else:
                    return Response(response.parsejson("business_phone_no is required", "", status=403))

                if "business_mobile_no" in data and data['business_mobile_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(mobile_no=data['business_mobile_no']).first()
                    if user_business_profile:
                        # Translators: This message appears when phone no already in db
                        return Response(response.parsejson("Business Mobile no already exist", "", status=403))
                    business_data['mobile_no'] = data['business_mobile_no']

                if "business_email" in data and data['business_email'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(email=data['business_email']).first()
                    if user_business_profile:
                        # Translators: This message appears when email already in business db
                        return Response(response.parsejson("Business Email already exist", "", status=403))
                    try:
                        validate_email(data['business_email'])
                    except ValidationError:
                        # Translators: This message appears when email is invalid
                        return Response(response.parsejson("Invalid business email address", "", status=404))
                    business_data['email'] = data['business_email']
                else:
                    return Response(response.parsejson("business_email is required", "", status=403))

                if "licence_no" in data and data['licence_no'] != "":
                    business_data['licence_no'] = data['licence_no']
                else:
                    return Response(response.parsejson("licence_no is required", "", status=403))

                if "address_first" in data and data['address_first'] != "":
                    # business_data['address_first'] = data['address_first']
                    address_first = data['address_first']
                else:
                    return Response(response.parsejson("address_first is required", "", status=403))

                if "state" in data and data['state'] != "":
                    # business_data['state'] = data['state']
                    state = data['state']
                else:
                    return Response(response.parsejson("state is required", "", status=403))

                if "business_country" in data and data['business_country'] != "":
                    business_data['country'] = int(data['business_country'])
                else:
                    # business_data['country'] = None
                    return Response(response.parsejson("business_country is required", "", status=403))
                # ----------------Find country from state----------------
                try:
                    lookup_state = LookupState.objects.filter(id=int(state)).first()
                    lookup_state_name = lookup_state.state_name
                    # geolocator = Nominatim(user_agent="geoapiExercises")
                    geolocator = Nominatim(user_agent="google")
                    location = geolocator.geocode(lookup_state.state_name)
                    location_country = location.address.split(',')
                    location_country = location_country[-1].strip()
                except Exception as exp:
                    location_country = None


                if "postal_code" in data and data['postal_code'] != "":
                    # business_data['postal_code'] = data['postal_code']
                    postal_code = data['postal_code']
                else:
                    return Response(response.parsejson("postal_code is required", "", status=403))
            with transaction.atomic():
                domain_url = ""
                login_data = {}
                # -----------------------Activate token----------------------
                activate_token = forgot_token()
                if not activate_token:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))

                serializer = UsersSerializer(data=data)
                if serializer.is_valid():
                    serializer.validated_data['status_id'] = 2
                    serializer.validated_data['activation_code'] = activate_token
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))

                    try:
                        if user_type == 1 and user_id > 0 and register_site is not None:
                            network_user_register = NetworkUser()
                            network_user_register.domain_id = register_site
                            network_user_register.user_id = user_id
                            network_user_register.status_id = 1
                            network_user_register.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))

                    # ------------Save Business Information-----------
                    if user_type == 2 and user_id > 0:
                        business_data['user'] = user_id
                        business_data['status'] = 1
                        serializer = UserBusinessProfileSerializer(data=business_data)
                        if serializer.is_valid():
                            serializer.validated_data['status_id'] = 1
                            serializer.save()

                            # ---------------Profile address------------
                            profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                                    "state": state, "postal_code": postal_code, "status": 1,
                                                    "added_by": user_id, "updated_by": user_id}
                            serializer = ProfileAddressSerializer(data=profile_address_data)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                # copy_errors.update(user_profile_serializer.errors)
                                return Response(response.parsejson(copy_errors, "", status=403))

                            # ---------------Save Domain Network-----------
                            network_data = {}
                            subdomain_url = settings.SUBDOMAIN_URL
                            domain_name = make_subdomain(company_name)
                            domain_url = subdomain_url.replace("###", domain_name)
                            network_data['domain_type'] = 2
                            network_data['domain_name'] = domain_name
                            network_data['domain_url'] = domain_url
                            network_data['is_active'] = 1
                            serializer = NetworkDomainSerializer(data=network_data)
                            if serializer.is_valid():
                                network = serializer.save()
                                network_id = network.id

                                # ------------------User Subscription plan updated-------------
                                user_subscription_data = {}
                                plan_pricing = PlanPricing.objects.filter(id=settings.FREE_PLAN_ID).first()
                                if plan_pricing is None:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson("Subscription plan not exist.", "", status=403))
                                default_theme = ThemesAvailable.objects.filter(is_active=1, is_default=1).first()
                                user_subscription_data['theme'] = None
                                if default_theme is not None:
                                    user_subscription_data['theme'] = default_theme.id

                                user_subscription_data['user'] = user_id
                                user_subscription_data['domain'] = network_id
                                user_subscription_data['opted_plan'] = plan_pricing.id
                                user_subscription_data['is_free'] = 1
                                user_subscription_data['payment_amount'] = plan_pricing.cost
                                user_subscription_data['payment_status'] = 1
                                user_subscription_data['subscription_status'] = 1
                                user_subscription_data['added_by'] = user_id
                                serializer = UserSubscriptionSerializer(data=user_subscription_data)
                                if serializer.is_valid():
                                    serializer.save()
                                    if default_theme is not None:
                                        user_theme_data = {}
                                        user_theme_data['domain'] = network_id
                                        user_theme_data['theme'] = default_theme.id
                                        user_theme_data['status'] = 1
                                        serializer = UserThemeSerializer(data=user_theme_data)
                                        if serializer.is_valid():
                                            serializer.save()
                                        else:
                                            transaction.set_rollback(True)  # -----Rollback Transaction----
                                            copy_errors = serializer.errors.copy()
                                            return Response(response.parsejson(copy_errors, "", status=403))

                                else:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    copy_errors = serializer.errors.copy()
                                    return Response(response.parsejson(copy_errors, "", status=403))

                                # -----------------Permission----------------
                                try:
                                    permission = [5, 7]
                                    for permission_data in permission:
                                        user_permission = UserPermission()
                                        user_permission.domain_id = network_id
                                        user_permission.user_id = user_id
                                        user_permission.permission_id = permission_data
                                        user_permission.is_permission = 1
                                        user_permission.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))

                                try:
                                    # ------------Login Data------------
                                    users_data = Users.objects.filter(id=user_id).first()
                                    login_data['user_id'] = users_data.id
                                    login_data['email'] = users_data.email
                                    login_data['site_id'] = network_id
                                    login_data['first_name'] = users_data.first_name
                                    login_data['user_type'] = users_data.user_type_id

                                    users_data.last_login = timezone.now()  # ----Update User Table---
                                    users_data.site_id = network_id  # ----Update User Table---
                                    users_data.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))
                        # -----------Set email template-------
                        try:
                            notification_template = NotificationTemplate.objects.filter(site__isnull=True, status=1)
                            if notification_template is not None:
                                for template in notification_template:
                                    new_template = NotificationTemplate()
                                    new_template.site_id = network_id
                                    new_template.event_id = template.event_id
                                    new_template.email_subject = template.email_subject
                                    new_template.email_content = template.email_content
                                    new_template.notification_text = template.notification_text
                                    new_template.push_notification_text = template.push_notification_text
                                    new_template.added_by_id = user_id
                                    new_template.updated_by_id = user_id
                                    new_template.status_id = 1
                                    new_template.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))
                        # ---------------Set bot--------------
                        try:
                            property_type = [1, 2, 3]
                            for property_type_id in property_type:
                                property_evaluator_setting = PropertyEvaluatorSetting()
                                property_evaluator_setting.domain_id = network_id
                                property_evaluator_setting.property_type_id = property_type_id
                                property_evaluator_setting.status_id = 1
                                property_evaluator_setting.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

            # ------------------------Email-----------------------
            activation_link = settings.RESET_PASSWORD_URL + "/activation/?token=" + str(activate_token)
            template_data = {"domain_id": "", "slug": "default_welcome"}
            admin_data = Users.objects.get(user_type=3)
            admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
            admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
            admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
            admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
            # admin_name = admin_data.first_name if admin_data.first_name is not None else ""
            # admin_email = admin_data.email if admin_data.email is not None else ""
            extra_data = {"user_name": first_name,
                          "activation_link": activation_link,
                          "web_url": settings.FRONT_BASE_URL,
                          "user_type": user_type_name,
                          "domain_name": "Bidhom",
                          "user_email": email,
                          "user_password": phone_no,
                          "admin_name": admin_name,
                          "admin_email": admin_email,
                          "sub_domain": domain_name,
                          "domain_url": domain_url
                          }
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            all_data = {}
            if user_type == 2 and user_id > 0:
                token = oauth_token(user_id, phone_no)
                login_data['auth_token'] = token
            all_data['domain_url'] = domain_url
            all_data['login_data'] = login_data
            return Response(response.parsejson("User Registered Successfully", all_data, status=201))
        except Exception as exp:
            print(exp)
            return Response(response.parsejson(str(exp), exp, status=403))


class NewUserRegistrationApiView(APIView):
    """
    New User Registration
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    # @transaction.atomic
    # @staticmethod
    def post(self, request):
        try:
            data = request.data
            user_type_name = 'Buyer/Seller'
            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if "user_behaviour" in data and data['user_behaviour'] != "":
                user_behaviour = int(data['user_behaviour'])
            else:
                return Response(response.parsejson("user_behaviour is required", "", status=403))

            register_site = None
            if "register_site" in data and data['register_site'] != "":
                register_site = int(data['register_site'])
                network = NetworkDomain.objects.filter(id=register_site, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Registered site not exist.", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                users = Users.objects.filter(phone_no=phone_no).first()
                # if users:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if phone_no:
                hashed_pwd = make_password(str(phone_no))
                data['password'] = hashed_pwd
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            data['encrypted_password'] = b64encode(str(phone_no))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))
            # create_dummy_property = 0
            # if "create_dummy_property" in data and data['create_dummy_property'] != "":
            #     create_dummy_property = int(data['create_dummy_property'])

            # -------------Check Data for Agent/Broker Only----------------
            if user_type == 2:
                user_type_name = 'Agent/Broker'
                business_data = {}
                if "business_first_name" in data and data['business_first_name'] != "":
                    business_data['first_name'] = data['business_first_name']
                else:
                    return Response(response.parsejson("business_first_name is required", "", status=403))

                if "business_last_name" in data and data['business_last_name'] != "":
                    business_data['last_name'] = data['business_last_name']
                else:
                    return Response(response.parsejson("business_last_name is required", "", status=403))

                if "company_name" in data and data['company_name'] != "":
                    company_name = data['company_name']
                    business_data['company_name'] = data['company_name']
                else:
                    return Response(response.parsejson("company_name is required", "", status=403))

                if "business_phone_no" in data and data['business_phone_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(phone_no=data['business_phone_no']).first()
                    # if user_business_profile:
                    #     # Translators: This message appears when phone no already in db
                    #     return Response(response.parsejson("Business Phone no already exist", "", status=403))
                    business_data['phone_no'] = data['business_phone_no']
                else:
                    return Response(response.parsejson("business_phone_no is required", "", status=403))

                if "business_mobile_no" in data and data['business_mobile_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(mobile_no=data['business_mobile_no']).first()
                    if user_business_profile:
                        # Translators: This message appears when phone no already in db
                        return Response(response.parsejson("Business Mobile no already exist", "", status=403))
                    business_data['mobile_no'] = data['business_mobile_no']

                if "business_email" in data and data['business_email'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(email=data['business_email']).first()
                    if user_business_profile:
                        # Translators: This message appears when email already in business db
                        return Response(response.parsejson("Business Email already exist", "", status=403))
                    try:
                        validate_email(data['business_email'])
                    except ValidationError:
                        # Translators: This message appears when email is invalid
                        return Response(response.parsejson("Invalid business email address", "", status=404))
                    business_data['email'] = data['business_email']
                else:
                    return Response(response.parsejson("business_email is required", "", status=403))

                if "licence_no" in data and data['licence_no'] != "":
                    business_data['licence_no'] = data['licence_no']
                else:
                    return Response(response.parsejson("licence_no is required", "", status=403))

                if "address_first" in data and data['address_first'] != "":
                    # business_data['address_first'] = data['address_first']
                    address_first = data['address_first']
                else:
                    return Response(response.parsejson("address_first is required", "", status=403))

                if "state" in data and data['state'] != "":
                    # business_data['state'] = data['state']
                    state = data['state']
                else:
                    return Response(response.parsejson("state is required", "", status=403))

                if "business_country" in data and data['business_country'] != "":
                    business_data['country'] = int(data['business_country'])
                    # business_country = int(data['business_country'])
                else:
                    # business_data['business_country'] = None
                    return Response(response.parsejson("business_country is required", "", status=403))
                # ----------------Find country from state----------------
                try:
                    lookup_state = LookupState.objects.filter(id=int(state)).first()
                    lookup_state_name = lookup_state.state_name
                    # geolocator = Nominatim(user_agent="geoapiExercises")
                    geolocator = Nominatim(user_agent="google")
                    location = geolocator.geocode(lookup_state.state_name)
                    location_country = location.address.split(',')
                    location_country = location_country[-1].strip()
                except Exception as exp:
                    location_country = None


                if "postal_code" in data and data['postal_code'] != "":
                    # business_data['postal_code'] = data['postal_code']
                    postal_code = data['postal_code']
                else:
                    return Response(response.parsejson("postal_code is required", "", status=403))
            with transaction.atomic():
                domain_url = ""
                login_data = {}
                # -----------------------Activate token----------------------
                activate_token = forgot_token()
                if not activate_token:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))

                # -----------------------Verification token----------------------
                verification_token = forgot_token()
                if not verification_token:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))

                serializer = UsersSerializer(data=data)
                if serializer.is_valid():
                    # serializer.validated_data['status_id'] = 2
                    serializer.validated_data['status_id'] = 1
                    serializer.validated_data['activation_code'] = activate_token
                    serializer.validated_data['activation_date'] = timezone.now()
                    serializer.validated_data['verification_code'] = verification_token
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))

                    try:
                        if user_type == 1 and user_id > 0 and register_site is not None:
                            network_user_register = NetworkUser()
                            network_user_register.domain_id = register_site
                            network_user_register.user_id = user_id
                            network_user_register.status_id = 1
                            network_user_register.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))

                    # ------------Save Business Information-----------
                    if user_type == 2 and user_id > 0:
                        business_data['user'] = user_id
                        business_data['status'] = 1
                        serializer = UserBusinessProfileSerializer(data=business_data)
                        if serializer.is_valid():
                            serializer.validated_data['status_id'] = 1
                            serializer.save()

                            # ---------------Profile address------------
                            profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                                    "state": state, "postal_code": postal_code, "status": 1,
                                                    "added_by": user_id, "updated_by": user_id}
                            serializer = ProfileAddressSerializer(data=profile_address_data)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                # copy_errors.update(user_profile_serializer.errors)
                                return Response(response.parsejson(copy_errors, "", status=403))

                            # ---------------Save Domain Network-----------
                            network_data = {}
                            subdomain_url = settings.SUBDOMAIN_URL
                            domain_name = make_subdomain(company_name)
                            domain_url = subdomain_url.replace("###", domain_name)
                            network_data['domain_type'] = 2
                            network_data['domain_name'] = domain_name
                            network_data['domain_url'] = domain_url
                            network_data['is_active'] = 1
                            serializer = NetworkDomainSerializer(data=network_data)
                            if serializer.is_valid():
                                network = serializer.save()
                                network_id = network.id

                                # ------------------User Subscription plan updated-------------
                                user_subscription_data = {}
                                if user_behaviour == 1:
                                    plan_pricing = PlanPricing.objects.filter(id=settings.AGENT_PLAN_ID).first()
                                elif user_behaviour == 2:
                                    plan_pricing = PlanPricing.objects.filter(id=settings.BROKER_PLAN_ID).first()
                                else:
                                    plan_pricing = PlanPricing.objects.filter(id=settings.FREE_PLAN_ID).first()
                                # plan_pricing = PlanPricing.objects.filter(id=settings.FREE_PLAN_ID).first()
                                if plan_pricing is None:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson("Subscription plan not exist.", "", status=403))
                                default_theme = ThemesAvailable.objects.filter(is_active=1, is_default=1).first()
                                user_subscription_data['theme'] = None
                                if default_theme is not None:
                                    user_subscription_data['theme'] = default_theme.id

                                user_subscription_data['user'] = user_id
                                user_subscription_data['domain'] = network_id
                                user_subscription_data['opted_plan'] = plan_pricing.id
                                # user_subscription_data['is_free'] = 1
                                user_subscription_data['payment_amount'] = plan_pricing.cost
                                user_subscription_data['payment_status'] = 1
                                user_subscription_data['subscription_status'] = 1
                                user_subscription_data['added_by'] = user_id
                                user_subscription_data['is_first_subscription'] = 1
                                user_subscription_data['start_date'] = timezone.now()
                                user_subscription_data['end_date'] = timezone.now() + timezone.timedelta(days=plan_pricing.plan_type.duration_in_days)
                                serializer = UserSubscriptionSerializer(data=user_subscription_data)
                                if serializer.is_valid():
                                    serializer.save()
                                    if default_theme is not None:
                                        user_theme_data = {}
                                        user_theme_data['domain'] = network_id
                                        user_theme_data['theme'] = default_theme.id
                                        user_theme_data['status'] = 1
                                        serializer = UserThemeSerializer(data=user_theme_data)
                                        if serializer.is_valid():
                                            serializer.save()
                                        else:
                                            transaction.set_rollback(True)  # -----Rollback Transaction----
                                            copy_errors = serializer.errors.copy()
                                            return Response(response.parsejson(copy_errors, "", status=403))

                                else:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    copy_errors = serializer.errors.copy()
                                    return Response(response.parsejson(copy_errors, "", status=403))

                                # -----------------Permission----------------
                                try:
                                    if user_behaviour == 1:
                                        permission = [2, 3, 4, 5, 6, 7, 11]
                                    elif user_behaviour == 2:
                                        permission = [1, 2, 3, 4, 5, 6, 7, 11, 12, 15, 16]
                                    else:
                                        permission = [5, 7]
                                    # permission = [5, 7]
                                    for permission_data in permission:
                                        user_permission = UserPermission()
                                        user_permission.domain_id = network_id
                                        user_permission.user_id = user_id
                                        user_permission.permission_id = permission_data
                                        user_permission.is_permission = 1
                                        user_permission.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))

                                try:
                                    # ------------Login Data------------
                                    users_data = Users.objects.filter(id=user_id).first()
                                    login_data['user_id'] = users_data.id
                                    login_data['email'] = users_data.email
                                    login_data['site_id'] = network_id
                                    login_data['first_name'] = users_data.first_name
                                    login_data['user_type'] = users_data.user_type_id

                                    users_data.last_login = timezone.now()  # ----Update User Table---
                                    users_data.site_id = network_id  # ----Update User Table---
                                    users_data.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))
                        # -----------Set email template-------
                        try:
                            notification_template = NotificationTemplate.objects.filter(site__isnull=True, status=1)
                            if notification_template is not None:
                                for template in notification_template:
                                    new_template = NotificationTemplate()
                                    new_template.site_id = network_id
                                    new_template.event_id = template.event_id
                                    new_template.email_subject = template.email_subject
                                    new_template.email_content = template.email_content
                                    new_template.notification_text = template.notification_text
                                    new_template.push_notification_text = template.push_notification_text
                                    new_template.added_by_id = user_id
                                    new_template.updated_by_id = user_id
                                    new_template.status_id = 1
                                    new_template.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))
                        # ---------------Set bot--------------
                        try:
                            property_type = [1, 2, 3]
                            for property_type_id in property_type:
                                property_evaluator_setting = PropertyEvaluatorSetting()
                                property_evaluator_setting.domain_id = network_id
                                property_evaluator_setting.property_type_id = property_type_id
                                property_evaluator_setting.status_id = 1
                                property_evaluator_setting.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))
                    # -------------Create Property---------------
                    # if create_dummy_property:
                    #     self.create_property(network_id, user_id)
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
                
            # ------------------------Email-----------------------
            verification_link = settings.RESET_PASSWORD_URL + "/email-verification/?token=" + str(verification_token)
            template_data = {"domain_id": "", "slug": "default_email_verification"}
            admin_data = Users.objects.get(user_type=3)
            admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
            admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
            admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
            admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
            # admin_name = admin_data.first_name if admin_data.first_name is not None else ""
            # admin_email = admin_data.email if admin_data.email is not None else ""
            extra_data = {"user_name": first_name,
                          "verification_link": verification_link,
                          "web_url": settings.FRONT_BASE_URL,
                          "user_type": user_type_name,
                          "domain_name": "Bidhom",
                          "user_email": email,
                          "user_password": phone_no,
                          "admin_name": admin_name,
                          "admin_email": admin_email,
                          "sub_domain": domain_name,
                          "domain_url": domain_url
                          }
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            all_data = {}
            if user_type == 2 and user_id > 0:
                token = oauth_token(user_id, phone_no)
                login_data['auth_token'] = token
            all_data['domain_url'] = domain_url
            all_data['login_data'] = login_data
            return Response(response.parsejson("User Registered Successfully", all_data, status=201))
        except Exception as exp:
            print(exp)
            return Response(response.parsejson(str(exp), exp, status=403))

    @staticmethod
    def create_property(domain_id, user_id):
    # def get(request):
        try:
            # domain_id, user_id, country_id = 68, 111, 1
            listing_data = {
                "title": "testing",
                "description": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard",
                "domain": domain_id,
                "agent": user_id,
                "property_asset": 3,
                "property_type": 4,
                "sale_by_type": 1,
                "beds": 4,
                "baths": 4,
                "year_built": 2021,
                "square_footage": 2800,
                "address_one": "47 W 13th St",
                "city": "New York",
                "postal_code": "10011",
                "is_approved": True,
                "state": 19,
                "country": 1,
                "status": 1
            }
            auction = {
                "domain": domain_id,
                "property": 123,
                "reserve_amount": 1000000,
                "bid_increments": 1000,
                "status": 1,
                "start_price": 10000,
                "auction": 1,
                "start_date": timezone.now() + timezone.timedelta(7),
                "end_date": timezone.now() + timezone.timedelta(37)
            }
            with transaction.atomic():
                serializer = AddDummyPropertySerializer(data=listing_data)
                if serializer.is_valid():
                    property_data = serializer.save()
                    property_id = property_data.id
                    auction['property'] = property_id
                    serializer = AddDummyAuctionSerializer(data=auction)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        copy_errors = serializer.errors.copy()
                        print(copy_errors)
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                    uploads = {
                        "upload": 7879,
                        "property": property_id,
                        "upload_type": 1,
                        "status": 1
                    }

                    serializer = AddPropertyUploadsSerializer(data=uploads)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        copy_errors = serializer.errors.copy()
                        print(copy_errors)
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                else:
                    copy_errors = serializer.errors.copy()
                    print(copy_errors)
                    transaction.set_rollback(True)  # -----Rollback Transaction----
            # return Response(response.parsejson("Success", "", status=403))
            return True
        except Exception as exp:
            print(exp)
            return False
            # return Response(response.parsejson("Success", "", status=403))


class CreateDummyPropertyApiView(APIView):
    """
    Create Dummy Property
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            listing_data = {
                "title": "testing",
                "description": "Great location with a huge backyard and open living spaces. This home needs a new owner to do the work needed. Bring your fresh ideas to make this home uniquely yours. Garden areas have been organically cultivated with compost over the years to amend and enhance.  There are well established decorative gardens, as well as organic perennial edible gardens; to include blackberries, elderberry, strawberry, currants, sage, thyme, oregano, mint, lemon balm, rhubarb, spring onions.",
                "domain": domain_id,
                "agent": user_id,
                "property_asset": 3,
                "property_type": 4,
                "sale_by_type": 1,
                "beds": 10,
                "baths": 6,
                "year_built": 2023,
                "square_footage": 2800,
                "address_one": "47 W 13th St",
                "city": "New York",
                "postal_code": "10011",
                "is_approved": True,
                "state": 19,
                "country": 1,
                "status": 1,
                "year_renovated": 2023,
                "lot_size": 2800,
                "lot_size_unit": 2,
                "lot_dimensions": 2800,
                "broker_co_op": True,
                "financing_available": True,
                "home_warranty": True,
                "basement": True,
                "county": "",
                "subdivision": "",
                "school_district": "",
                "property_taxes": 4,
                "special_assessment_tax": 4,
                "hoa_fee": 4.00,
                "garage_spaces": 600,
                "main_floor_area": 2800,
                "upper_floor_area": 2800,
                "basement_area": 2800,
                "main_floor_bedroom": 4,
                "upper_floor_bedroom": 4,
                "basement_bedroom": 2,
                "main_floor_bathroom": 2,
                "upper_floor_bathroom": 2,
                "basement_bathroom": 2,
                "fireplace": 4,
                "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
            }
            auction = {
                "domain": domain_id,
                "property": 123,
                "reserve_amount": 1000000,
                "bid_increments": 1000,
                "status": 1,
                "start_price": 10000,
                "auction": 1,
                "start_date": timezone.now() + timezone.timedelta(7),
                "end_date": timezone.now() + timezone.timedelta(37)
            }
            with transaction.atomic():
                serializer = AddDummyPropertySerializer(data=listing_data)
                if serializer.is_valid():
                    property_data = serializer.save()
                    property_id = property_data.id
                    auction['property'] = property_id
                    serializer = AddDummyAuctionSerializer(data=auction)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        copy_errors = serializer.errors.copy()
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(copy_errors, "", status=403))
                    uploads = [{
                        # "upload": 7879,
                        "upload": 1051,
                        "property": property_id,
                        "upload_type": 1,
                        "status": 1
                    }, {
                        # "upload": 7879,
                        "upload": 1052,
                        "property": property_id,
                        "upload_type": 1,
                        "status": 1
                    }, {
                        # "upload": 7879,
                        "upload": 1055,
                        "property": property_id,
                        "upload_type": 1,
                        "status": 1
                    }
                    ]
                    for upload in uploads:
                        serializer = AddPropertyUploadsSerializer(data=upload)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            copy_errors = serializer.errors.copy()
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(copy_errors, "", status=403))

                    properties_video = [1098, 1098, 1098]
                    for video in properties_video:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = video
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 2
                        property_uploads.status_id = 1
                        property_uploads.save()

                    properties_documents = [1067, 1067, 1067]
                    for documents in properties_documents:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = documents
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 3
                        property_uploads.status_id = 1
                        property_uploads.save()

                    # ------------------Property Term Accepted------------------
                    update = PropertyTermAccepted()
                    update.property_id = property_id
                    update.term_accepted_id = 12
                    update.save()

                    # ------------------Property Occupation------------------
                    update = PropertyOccupiedBy()
                    update.property_id = property_id
                    update.occupied_by_id = 4
                    update.save()

                    # ------------------Ownership------------------
                    update = PropertyOwnership()
                    update.property_id = property_id
                    update.ownership_id = 4
                    update.save()

                    # ------------------Possession------------------
                    update = PropertyPossession()
                    update.property_id = property_id
                    update.possession_id = 1
                    update.save()

                    # ------------------Style------------------
                    update = PropertyStyle()
                    update.property_id = property_id
                    update.style_id = 18
                    update.save()

                    # ------------------Stories------------------
                    update = PropertyStories()
                    update.property_id = property_id
                    update.stories_id = 6
                    update.save()

                    # ------------------Recent Updates------------------
                    update = PropertyRecentUpdates()
                    update.property_id = property_id
                    update.recent_updates_id = 21
                    update.save()

                    # ------------------Security Features------------------
                    update = PropertySecurityFeatures()
                    update.property_id = property_id
                    update.security_features_id = 8
                    update.save()

                    # ------------------Cooling------------------
                    update = PropertyCooling()
                    update.property_id = property_id
                    update.cooling_id = 12
                    update.save()

                    # ------------------Heating------------------
                    update = PropertyHeating()
                    update.property_id = property_id
                    update.heating_id = 21
                    update.save()

                    # ------------------Electric------------------
                    update = PropertyElectric()
                    update.property_id = property_id
                    update.electric_id = 2
                    update.save()

                    # ------------------Gas------------------
                    update = PropertyGas()
                    update.property_id = property_id
                    update.gas_id = 3
                    update.save()

                    # ------------------Water------------------
                    update = PropertyWater()
                    update.property_id = property_id
                    update.water_id = 3
                    update.save()

                    # ------------------Sewer------------------
                    update = PropertySewer()
                    update.property_id = property_id
                    update.sewer_id = 3
                    update.save()

                    # ------------------Zoning------------------
                    update = PropertyZoning()
                    update.property_id = property_id
                    update.zoning_id = 4
                    update.save()

                    # ------------------Tax Exemptions------------------
                    update = PropertyTaxExemptions()
                    update.property_id = property_id
                    update.tax_exemptions_id = 2
                    update.save()

                    # ------------------Kitchen Features------------------
                    update = PropertyKitchenFeatures()
                    update.property_id = property_id
                    update.kitchen_features_id = 8
                    update.save()

                    # ------------------Appliances------------------
                    update = PropertyAppliances()
                    update.property_id = property_id
                    update.appliances_id = 24
                    update.save()

                    # ------------------Flooring------------------
                    update = PropertyFlooring()
                    update.property_id = property_id
                    update.flooring_id = 8
                    update.save()

                    # ------------------Windows------------------
                    update = PropertyWindows()
                    update.property_id = property_id
                    update.windows_id = 4
                    update.save()

                    # ------------------Bedroom Features------------------
                    update = PropertyBedroomFeatures()
                    update.property_id = property_id
                    update.bedroom_features_id = 6
                    update.save()

                    # ------------------Bathroom Features------------------
                    update = PropertyBathroomFeatures()
                    update.property_id = property_id
                    update.bathroom_features_id = 10
                    update.save()

                    # ------------------Master Bedroom Features------------------
                    update = PropertyMasterBedroomFeatures()
                    update.property_id = property_id
                    update.master_bedroom_features_id = 18
                    update.save()

                    # ------------------Basement Features------------------
                    update = PropertyBasementFeatures()
                    update.property_id = property_id
                    update.basement_features_id = 17
                    update.save()

                    # ------------------Other Rooms------------------
                    update = PropertyOtherRooms()
                    update.property_id = property_id
                    update.other_rooms_id = 12
                    update.save()

                    # ------------------Other Features------------------
                    update = PropertyOtherFeatures()
                    update.property_id = property_id
                    update.other_features_id = 8
                    update.save()

                    # ------------------Fire Place Unit------------------
                    update = PropertyFireplaceType()
                    update.property_id = property_id
                    update.fireplace_type_id = 3
                    update.save()

                    # ------------------Handicap Amenities------------------
                    update = PropertyHandicapAmenities()
                    update.property_id = property_id
                    update.handicap_amenities_id = 13
                    update.save()

                    # ------------------Construction------------------
                    update = PropertyConstruction()
                    update.property_id = property_id
                    update.construction_id = 13
                    update.save()

                    # ------------------Exterior Features------------------
                    update = PropertyExteriorFeatures()
                    update.property_id = property_id
                    update.exterior_features_id = 20
                    update.save()

                    # ------------------Roof------------------
                    update = PropertyRoof()
                    update.property_id = property_id
                    update.roof_id = 4
                    update.save()

                    # ------------------Foundation------------------
                    update = PropertyFoundation()
                    update.property_id = property_id
                    update.foundation_id = 2
                    update.save()

                    # ------------------Fence------------------
                    update = PropertyFence()
                    update.property_id = property_id
                    update.fence_id = 2
                    update.save()

                    # ------------------Pool------------------
                    update = PropertyPool()
                    update.property_id = property_id
                    update.pool_id = 3
                    update.save()

                    # ------------------Garage Parking------------------
                    update = PropertyGarageParking()
                    update.property_id = property_id
                    update.garage_parking_id = 3
                    update.save()

                    # ------------------Garage Features------------------
                    update = PropertyGarageFeatures()
                    update.property_id = property_id
                    update.garage_features_id = 18
                    update.save()

                    # ------------------Out Buildings------------------
                    update = PropertyOutbuildings()
                    update.property_id = property_id
                    update.outbuildings_id = 3
                    update.save()

                    # ------------------Location Features------------------
                    update = PropertyLocationFeatures()
                    update.property_id = property_id
                    update.location_features_id = 13
                    update.save()

                    # ------------------Property Faces------------------
                    update = PropertyPropertyFaces()
                    update.property_id = property_id
                    update.property_faces_id = 2
                    update.save()
                else:
                    copy_errors = serializer.errors.copy()
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(copy_errors, "", status=403))

            return Response(response.parsejson("Property Successfully Created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TempUserRegistrationApiView(APIView):
    """
    Temp User Registration
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    # @transaction.atomic
    @staticmethod
    def post(request):
        try:
            data = request.data
            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = data['phone_no']
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            # if x_forwarded_for:
            #     ip = x_forwarded_for.split(',')[0]
            # else:
            #     ip = request.META.get('REMOTE_ADDR')
            # print(ip)

            temp_user = TempRegistration()
            temp_user.first_name = first_name
            temp_user.last_name = last_name
            temp_user.email = email
            temp_user.phone_no = phone_no
            temp_user.save()
            return Response(response.parsejson("Temp User Registration Data Save Successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainRegistrationApiView(APIView):
    """
    Subdomain Registration
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    # @transaction.atomic
    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                domain_url = network.domain_url
                user_subscription = UserSubscription.objects.filter(domain=domain_id, subscription_status=1).last()
                if user_subscription is None:
                    return Response(response.parsejson("Currently can't create account on domain.", "", status=403))
                # elif user_subscription is not None and user_subscription.opted_plan.subscription_id != 4:
                #     return Response(response.parsejson("Currently can't create account on domain.", "", status=403))

                user = Users.objects.filter(site=domain_id).last()
                if user.status_id != 1:
                    return Response(response.parsejson("Currently can't create account on domain.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "described_by" in data and data['described_by'] != "":
                described_by = int(data['described_by'])
            else:
                return Response(response.parsejson("described_by is required", "", status=403))

            if described_by == 3:
                if "brokerage_name" in data and data['brokerage_name'] != "":
                    brokerage_name = data['brokerage_name']
                else:
                    return Response(response.parsejson("brokerage_name is required", "", status=403))

                if "licence_number" in data and data['licence_number'] != "":
                    licence_number = data['licence_number']
                else:
                    return Response(response.parsejson("licence_number is required", "", status=403))
            else:
                brokerage_name = None
                licence_number = None

            if "agree_term" in data and data['agree_term'] != "":
                agree_term = int(data['agree_term'])
                if agree_term != 1:
                    return Response(response.parsejson("Please accept term.", "", status=403))
            else:
                return Response(response.parsejson("agree_term is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                # users = Users.objects.filter(phone_no=phone_no).first()
                # if users:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
                hashed_pwd = make_password(str(password))
                data['password'] = hashed_pwd
                data['encrypted_password'] = b64encode(str(password))
            else:
                return Response(response.parsejson("password is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            with transaction.atomic():
                # -----------------------Activate token----------------------
                activate_token = forgot_token()
                if not activate_token:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))

                serializer = UsersSerializer(data=data)
                if serializer.is_valid():
                    serializer.validated_data['user_type_id'] = 1
                    serializer.validated_data['status_id'] = 2
                    serializer.validated_data['activation_code'] = activate_token
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))

                    try:
                        network_user_register = NetworkUser()
                        network_user_register.domain_id = domain_id
                        network_user_register.user_id = user_id
                        network_user_register.status_id = 1
                        network_user_register.brokerage_name = brokerage_name
                        network_user_register.licence_number = licence_number
                        network_user_register.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
            # ------------------------Email-----------------------
            # activation_link = domain_url + "activation/?token=" + str(activate_token)
            activation_link = settings.FRONT_URL + "/activation/?token=" + str(activate_token)
            template_data = {"domain_id": domain_id, "slug": "subdomain_user_addition"}
            admin_data = Users.objects.get(user_type=3)
            admin_name = admin_data.first_name if admin_data.first_name is not None else ""
            admin_email = admin_data.email if admin_data.email is not None else ""
            domain_name = network.domain_name
            user_type_name = ''
            if described_by == 1:
                user_type_name = 'Buyer'
            elif described_by == 2:
                user_type_name = 'Seller'
            elif described_by == 3:
                user_type_name = 'Broker/Agent'
            extra_data = {
                "user_name": first_name,
                "activation_link": activation_link,
                'web_url': settings.FRONT_BASE_URL,
                "domain_id": domain_id,
                "user_type": user_type_name,
                "domain_name": domain_name.title(),
                "user_email": email,
                "user_password": password,
                "admin_name": admin_name,
                "admin_email": admin_email  
                }
            d = compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            print(d)
            site_sttings = SiteSetting.objects.filter(settings_name="admin_email", is_active=1).first()
            all_data = {}
            if site_sttings is not None:
                all_data['admin_email'] = site_sttings.setting_value
            else:
                all_data['admin_email'] = ""
            return Response(response.parsejson("User Registered Successfully", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserRegistrationVerificationApiView(APIView):
    """
    User Registration Verification API
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "activation_code" in data and data['activation_code'] != "":
                activation_code = data['activation_code']
            else:
                # Translators: This message appears when activation_code is empty
                return Response(response.parsejson("activation_code is required", "", status=403))

            users = Users.objects.filter(activation_code=activation_code, activation_date__isnull=True).first()
            if users is None:
                return Response(response.parsejson("User already activated.", "", status=403))
            users.status_id = 1
            users.activation_date = timezone.now()
            users.save()

            return Response(response.parsejson("User activated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainRegistrationVerificationApiView(APIView):
    """
    Subdomain Registration Verification API
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                domain_url = network.domain_url
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "activation_code" in data and data['activation_code'] != "":
                activation_code = data['activation_code']
            else:
                # Translators: This message appears when activation_code is empty
                return Response(response.parsejson("activation_code is required", "", status=403))

            users = Users.objects.filter(activation_code=activation_code, network_user__domain=domain_id, network_user__status=1).first()
            if users is None:
                return Response(response.parsejson("Not site user.", "", status=403))
            elif users is not None and users.activation_date is not None:
                return Response(response.parsejson("Already activated.", "", status=403))
            users.status_id = 1
            users.activation_date = timezone.now()
            users.last_login = timezone.now()
            all_data = {}
            encrypted_password = users.encrypted_password
            encrypted_password = b64decode(encrypted_password)
            token = oauth_token(users.id, encrypted_password)
            all_data['auth_token'] = token
            all_data['user_id'] = users.id
            all_data['email'] = users.email
            all_data['site_id'] = users.site_id
            all_data['user_type'] = users.user_type_id
            all_data['first_name'] = users.first_name
            users.save()
            return Response(response.parsejson("User activated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LoginApiView(APIView):
    """
    User Login API
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                # Translators: This message appears when email is empty
                return Response(response.parsejson("email is required", "", status=403))

            try:
                validate_email(email)
            except ValidationError:
                # Translators: This message appears when email is invalid
                return Response(response.parsejson("Invalid email address", "", status=404))

            if "password" in data and data['password'] != "":
                password = data['password']
                # hashed_pwd = make_password(password)
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))

            if "user_type" in data and data['user_type'].lower() == "admin":
                users = Users.objects.filter(email__iexact=email, user_type__in=[3]).first()
            else:
                users = Users.objects.filter(email__iexact=email, user_type__in=[1, 2]).first()
                if users is not None and users.activation_date is None and users.activation_date == "":
                    return Response(response.parsejson("User not activated.", "", status=403))

            if users is None:
                return Response(response.parsejson("User not exist.", "", status=403))
            elif users.activation_date == "" or users.activation_date is None:
                return Response(response.parsejson("Email is not verified kindly verify your email first.", "", status=403))
            elif users.status_id != 1:
                return Response(response.parsejson("Your account is not active.", "", status=403))

            all_data = {}
            if check_password(password, users.password):
                token = oauth_token(users.id, password)
                all_data['auth_token'] = token
                all_data['user_id'] = users.id
                all_data['email'] = users.email
                all_data['site_id'] = users.site_id
                all_data['user_type'] = users.user_type_id
                all_data['first_name'] = users.first_name
                all_data['domain_id'] = users.site_id
                all_data['domain_url'] = users.site.domain_url if users.site_id is not None and users.site_id > 0 else ""
                users.last_login = timezone.now()
                users.save()

            else:
                return Response(response.parsejson("Wrong Password", "", status=403))

            return Response(response.parsejson("Login Successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainLoginApiView(APIView):
    """
    Subdomain login
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                # Translators: This message appears when email is empty
                return Response(response.parsejson("email is required", "", status=403))

            try:
                validate_email(email)
            except ValidationError:
                # Translators: This message appears when email is invalid
                return Response(response.parsejson("Invalid email address", "", status=404))

            if "password" in data and data['password'] != "":
                password = data['password']
                # hashed_pwd = make_password(password)
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                user = Users.objects.filter(site=domain_id).last()
                if not user.activation_date:
                    return Response(response.parsejson("Email is not verified kindly verify your email first.", "", status=403))
                elif user.status_id != 1:
                    return Response(response.parsejson("Website is not active.", "", status=403))

            else:
                return Response(response.parsejson("domain_id is required", "", status=403))
            users = Users.objects.filter(Q(email__iexact=email) & Q(user_type__in=[1, 2, 4])).first()

            if users is None:
                return Response(response.parsejson("User not exist.", "", status=403))
            else:
                if users and not users.activation_date:
                    return Response(response.parsejson("Email is not verified kindly verify your email first.", "", status=403))
                elif users.status_id != 1:
                    return Response(response.parsejson("Your account is not active.", "", status=403))

                if users.site_id is None or users.site_id == "":
                    user_subscription = UserSubscription.objects.filter(domain=domain_id, subscription_status=1).last()
                    if user_subscription is None:
                        return Response(response.parsejson("Currently can't login on domain.", "", status=403))
                    # elif user_subscription is not None and user_subscription.opted_plan.subscription_id != 4:
                    #     return Response(response.parsejson("Currently can't login on domain.", "", status=403))
                    network_user = NetworkUser.objects.filter(domain=domain_id, user=users.id).first()
                    if network_user is not None and network_user.status_id != 1:
                        return Response(response.parsejson("User not active.", "", status=403))

            all_data = {}
            if not check_password(password, users.password):
                return Response(response.parsejson("Wrong Password", "", status=403))

            token = oauth_token(users.id, password)
            all_data['auth_token'] = token
            all_data['user_id'] = users.id
            all_data['email'] = users.email
            all_data['site_id'] = domain_id
            all_data['first_name'] = users.first_name
            all_data['user_type'] = users.user_type_id
            all_data['stripe_customer_id'] = user.stripe_customer_id
            all_data['is_admin'] = False
            all_data['customer_site_id'] = users.site_id
            network_user = NetworkUser.objects.filter(domain=domain_id, user=users.id, is_agent=1, status=1).first()
            if network_user is not None:
                all_data['is_admin'] = True
            elif users.site_id is not None and users.site_id == domain_id:
                all_data['is_admin'] = True

            all_data['is_free_plan'] = False
            user_subscription = UserSubscription.objects.filter(domain=domain_id).last()
            if user_subscription is not None:
                all_data['is_free_plan'] = user_subscription.is_free

            if users.site is not None and users.site_id == domain_id:
                all_data['is_broker'] = True
            else:
                all_data['is_broker'] = False
            # ---------User Type-------
            if users.site is not None and users.site_id == domain_id:
                all_data['user_type_name'] = "Broker"
            elif network_user is not None:
                all_data['user_type_name'] = "Agent"
            else:
                all_data['user_type_name'] = "Buyer"
            try:
                profile_data = UserUploads.objects.get(id=int(users.profile_image))
                profile = {
                    "upload_id": profile_data.id,
                    "doc_file_name": profile_data.doc_file_name,
                    "bucket_name": profile_data.bucket_name
                }
                all_data['profile_image'] = profile
            except Exception as exp:
                all_data['profile_image'] = {}

            # --------------Check Broker/Agent First Login----------
            try:
                # network_owner = Users.objects.filter(id=users.id, site=domain_id, is_first_login=False).first()
                current_date = date.today()
                network_owner = Users.objects.annotate(days_difference=Func(Now() - F('added_on'), function='DATEDIFF', template='%(expressions)s')).filter(Q(id=users.id) & Q(site=domain_id) & Q(stripe_customer_id__isnull=True) & Q(stripe_subscription_id__isnull=True) & (Q(website_tour__date__lt=current_date) | Q(website_tour__isnull=True))).values('days_difference')[0: 1]
                if len(network_owner) > 0:
                    days_from_create = int(network_owner[0]['days_difference'].days)
                    if days_from_create < 31:
                        all_data['is_first_login'] = 1
                        # users.is_first_login = 1
                        users.website_tour = timezone.now()
                    else:
                        all_data['is_first_login'] = 0
                else:
                    all_data['is_first_login'] = 0
            except Exception as exp:
                all_data['is_first_login'] = 0

            users.last_login = timezone.now()
            users.save()
            return Response(response.parsejson("Login Successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class RefreshTokenApiView(APIView):
    """
    Get Refresh Token
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required", "", status=403))

            if "refresh_token" in data and data['refresh_token'] != "":
                refresh = data['refresh_token']
            else:
                # Translators: This message appears when refresh_token is empty
                return Response(response.parsejson("refresh_token is required", "", status=403))

            token = refresh_token(user_id, refresh)
            return Response(response.parsejson("Login Successfully.", token, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class RevokeTokenApiView(APIView):
    """
    Revoke Token
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required", "", status=403))

            if "token" in data and data['token'] != "":
                token = data['token']
            else:
                # Translators: This message appears when token is empty
                return Response(response.parsejson("token is required", "", status=403))

            revoke = revoke_token(user_id, token)
            if revoke:
                return Response(response.parsejson("Token Revoked.", "", status=201))
            else:
                return Response(response.parsejson("Token Not Revoked.", token, status=201))

        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class LoginDetailsApiView(APIView):
    """
    Login Details
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "token" in data and data['token'] != "":
                token = data['token']
            else:
                # Translators: This message appears when token is empty
                return Response(response.parsejson("token is required", "", status=403))

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            user_id = user_details(token)
            if user_id:
                users = Users.objects.filter(id=user_id, status=1).exclude(user_type=3).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("Invalid Token.", "", status=403))
            all_data = {}
            encrypted_password = users.encrypted_password
            encrypted_password = b64decode(encrypted_password)
            token = oauth_token(users.id, encrypted_password)
            all_data['auth_token'] = token
            all_data['user_id'] = users.id
            all_data['email'] = users.email
            all_data['site_id'] = site_id
            all_data['first_name'] = users.first_name
            all_data['user_type'] = users.user_type_id
            all_data['stripe_customer_id'] = users.stripe_customer_id
            all_data['is_admin'] = False
            all_data['customer_site_id'] = users.site_id
            network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1).first()
            if network_user is not None:
                all_data['is_admin'] = True
            elif users.site_id is not None and users.site_id == site_id:
                all_data['is_admin'] = True

            all_data['is_free_plan'] = False
            user_subscription = UserSubscription.objects.filter(domain=site_id).last()
            if user_subscription is not None:
                all_data['is_free_plan'] = user_subscription.is_free

            broker = Users.objects.filter(id=user_id, site=site_id).first()
            if broker is not None:
                all_data['is_broker'] = True
            else:
                all_data['is_broker'] = False

            # ---------User Type-------
            if users.site is not None and users.site_id == site_id:
                all_data['user_type_name'] = "Broker"
            elif network_user is not None:
                all_data['user_type_name'] = "Agent"
            else:
                all_data['user_type_name'] = "Buyer"
            try:
                profile_data = UserUploads.objects.get(id=int(users.profile_image))
                profile = {
                    "upload_id": profile_data.id,
                    "doc_file_name": profile_data.doc_file_name,
                    "bucket_name": profile_data.bucket_name
                }
                all_data['profile_image'] = profile
            except Exception as exp:
                all_data['profile_image'] = {}

            # --------------Check Broker/Agent First Login----------
            try:
                # network_owner = Users.objects.filter(id=user_id, site=site_id, is_first_login=False).first()
                # if network_owner is not None:
                #     all_data['is_first_login'] = 1
                #     Users.objects.filter(id=user_id, site=site_id).update(is_first_login=1)
                # else:
                #     all_data['is_first_login'] = 0
                current_date = date.today()
                # network_owner = Users.objects.annotate(days_difference=Func(Now() - F('added_on'), function='DATEDIFF', template='%(expressions)s')).filter(Q(id=user_id) & Q(site=site_id) & (Q(website_tour__date__lt=current_date) | Q(website_tour__isnull=True)))[0: 1]
                network_owner = Users.objects.annotate(days_difference=Func(Now() - F('added_on'), function='DATEDIFF', template='%(expressions)s')).filter(Q(id=user_id) & Q(site=site_id) & Q(stripe_customer_id__isnull=True) & Q(stripe_subscription_id__isnull=True) & (Q(website_tour__date__lt=current_date) | Q(website_tour__isnull=True))).values('days_difference')[0: 1]
                if len(network_owner) > 0:
                    days_from_create = int(network_owner[0]['days_difference'].days)
                    if days_from_create < 31:
                        all_data['is_first_login'] = 1
                        # users.is_first_login = 1
                        Users.objects.filter(id=user_id, site=site_id).update(website_tour=timezone.now())
                    else:
                        all_data['is_first_login'] = 0
                else:
                    all_data['is_first_login'] = 0
            except Exception as exp:
                all_data['is_first_login'] = 0

            return Response(response.parsejson("Login Successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChangePasswordApiView(APIView):
    """
    Change Password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))

            if "new_password" in data and data['new_password'] != "":
                new_password = data['new_password']
            else:
                # Translators: This message appears when new_password is empty
                return Response(response.parsejson("new_password is required", "", status=403))

            users = Users.objects.filter(id=user_id).first()
            if users is None:
                # Translators: This message appears when User not exist
                return Response(response.parsejson("User Not Exist", "", status=403))

            if password == new_password:
                return Response(response.parsejson("New password should be different from old password. ", "", status=403))

            if not check_password(password, users.password):
                # Translators: This message appears when password not match
                return Response(response.parsejson("Password not matched", "", status=403))

            # This is required for Oauth
            users.encrypted_password = b64encode(new_password)
            users.password = make_password(new_password)
            users.save()
            return Response(response.parsejson("Password successfully changed.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ForgotPasswordApiView(APIView):
    """
    Forgot Password
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            forgot_source = None
            if "forgot_source" in data and data['forgot_source'] != "":
                forgot_source = data['forgot_source'].strip().lower()

            if "email" in data and data['email'] != "":
                email = data['email']
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))

                users = Users.objects.filter(email__iexact=email).exclude(user_type=3).first()
                if forgot_source == "admin":
                    users = Users.objects.filter(email__iexact=email, user_type=3).first()

                if users is None:
                    # Translators: This message appears when email not matched with user
                    return Response(response.parsejson("User Not exist.", "", status=403))
                if users.status_id != 1:
                    # Translators: This message appears when user is not active
                    return Response(response.parsejson("User is blocked or deleted.", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            # ===================Inactive all exist user token================
            UserPasswordReset.objects.filter(user=users.id).update(is_active=0)
            reset_token = forgot_token()
            if not reset_token:
                return Response(response.parsejson("Getting Some Issue.", "", status=403))

            # Token entry
            user_password_reset = UserPasswordReset()
            user_password_reset.user_id = users.id
            user_password_reset.reset_token = reset_token
            user_password_reset.is_active = 1
            user_password_reset.added_by_id = users.id
            user_password_reset.save()
            reset_link = settings.RESET_PASSWORD_URL+"/reset-password/?token="+str(reset_token)
            if forgot_source == "admin":
                reset_link = settings.RESET_PASSWORD_URL+"/admin/reset-password/?token="+str(reset_token)
            # ------------------------Email-----------------------
            if int(users.user_type.id) == 2 and users.user_type.user_type == 'Agent/Broker':
                extra_data = {"user_name": users.first_name, "reset_password_link": reset_link, 'web_url': settings.FRONT_BASE_URL}
                template_data = {"domain_id": "", "slug": "forget_password"}
                compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)
            else:
                extra_data = {"user_name": users.first_name, "reset_link": reset_link, 'web_url': settings.FRONT_BASE_URL}
                template_data = {"domain_id": "", "slug": "password_forgot"}
                compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Password reset link sent successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainForgotPasswordApiView(APIView):
    """
    Subdomain forgot Password
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                domain_url = network.domain_url
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))

                users = Users.objects.filter(Q(email__iexact=email) & (Q(network_user__domain=domain_id) | Q(site=domain_id))).exclude(user_type=3).first()
                if users is None:
                    # Translators: This message appears when email not matched with user
                    return Response(response.parsejson("User Not exist.", "", status=403))
                if users.status_id != 1:
                    # Translators: This message appears when user is not active
                    return Response(response.parsejson("User is blocked or deleted.", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            # ===================Inactive all exist user token================
            UserPasswordReset.objects.filter(user=users.id).update(is_active=0)
            reset_token = forgot_token()
            if not reset_token:
                return Response(response.parsejson("Getting Some Issue.", "", status=403))

            # Token entry
            user_password_reset = UserPasswordReset()
            user_password_reset.user_id = users.id
            user_password_reset.reset_token = reset_token
            user_password_reset.is_active = 1
            user_password_reset.added_by_id = users.id
            user_password_reset.save()
            reset_link = domain_url+"reset-password/?token="+str(reset_token)
            # ------------------------Email-----------------------
            extra_data = {"user_name": users.first_name, "reset_link": reset_link, 'web_url': settings.FRONT_BASE_URL, "domain_id": domain_id}
            template_data = {"domain_id": domain_id, "slug": "password_forgot"}
            compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Password reset link sent successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ResetPasswordApiView(APIView):
    """
    Reset Password
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "reset_token" in data and data['reset_token'] != "":
                reset_token = data['reset_token']
            else:
                # Translators: This message appears when reset_token is empty
                return Response(response.parsejson("reset_token is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))
            five_m_ago = timezone.now() - timezone.timedelta(minutes=5)
            reset_token = UserPasswordReset.objects.filter(reset_token=reset_token, added_on__gte=five_m_ago, is_active=1).first()
            # Token Verification
            if reset_token is None:
                # Translators: This message appears when reset token not matched
                return Response(response.parsejson("Link has expired", "", status=403))

            users = Users.objects.filter(id=reset_token.added_by_id, status=1).first()
            if users is None:
                # Translators: This message appears when User not exist
                return Response(response.parsejson("User Not Exist", "", status=403))

            # This is required for Oauth
            users.encrypted_password = b64encode(password)
            users.password = make_password(password)
            users.save()
            # update token table
            reset_token.is_active = 0
            reset_token.save()
            #send email
            user_data = Users.objects.get(id=reset_token.added_by_id)
            user_name = user_data.first_name if user_data.first_name is not None else "" 
            user_email = user_data.email if user_data.email is not None else ""
            if users.user_type_id == 3:
                login_link = settings.FRONT_BASE_URL+"/admin/"
            else:
                login_link = settings.FRONT_BASE_URL+"/login/"
            try:
                template_data = {"domain_id": "", "slug": "password_reset"}
                extra_data = {'user_name': user_name, 'login_link': login_link, "domain_id": ""}
                if user_email != "":
                    compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            except Exception as exp:
                pass
            return Response(response.parsejson("Reset Password Successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainResetPasswordApiView(APIView):
    """
    Subdomain Reset Password
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when domain_id is empty
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "reset_token" in data and data['reset_token'] != "":
                reset_token = data['reset_token']
            else:
                # Translators: This message appears when reset_token is empty
                return Response(response.parsejson("reset_token is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))
            five_m_ago = timezone.now() - timezone.timedelta(minutes=5)
            reset_token = UserPasswordReset.objects.filter(reset_token=reset_token, added_on__gte=five_m_ago, is_active=1).first()

            # Token Verification
            if reset_token is None:
                # Translators: This message appears when reset token not matched
                return Response(response.parsejson("Link has expired", "", status=403))

            users = Users.objects.filter(Q(id=reset_token.added_by_id) & Q(status=1) & (Q(network_user__domain=domain_id) | Q(site=domain_id))).first()
            if users is None:
                # Translators: This message appears when User not exist
                return Response(response.parsejson("User Not Exist", "", status=403))

            # This is required for Oauth
            users.encrypted_password = b64encode(password)
            users.password = make_password(password)
            users.save()
            # update token table
            reset_token.is_active = 0
            reset_token.save()
            #send email
            user_data = Users.objects.get(id=reset_token.added_by_id)
            user_name = user_data.first_name if user_data.first_name is not None else "" 
            user_email = user_data.email if user_data.email is not None else ""
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            login_link = subdomain_url.replace("###", domain_name)+"login/"
            try:
                template_data = {"domain_id": domain_id, "slug": "password_reset"}
                extra_data = {'user_name': user_name, 'login_link': login_link, "domain_id": domain_id}
                if user_email != "":
                    compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            except Exception as exp:
                pass
            return Response(response.parsejson("Reset Password Successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckUserExistsApiView(APIView):
    """
    CheckUserExistsApiView
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        """ Method :Post
            Description :
                check if user email/phone already exists api
            Url :
                /api-users/check-user-exists/
            Params:
                :param 1:
                    email :: String
                :param 2:
                    phone :: String
                :param 3:
                    user_id :: String
                :param 4:
                    check_type :: String
        """
        try:
            data = request.data
            email = ""
            if "email" in data and data['email'] != "":
                email = data['email']

            phone = ""
            if "phone" in data and data['phone'] != "":
                phone = data['phone']

            user_id = ""
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            check_type = "main"
            if "check_type" in data and data['check_type'] != "":
                check_type = data['check_type']
                if 'check_type' in data and data['check_type'] in ["main", "business"]:
                    pass
                else:
                    return Response(response.parsejson("Invalid type", "", status=403))

            all_data = {}
            if email or phone:
                if check_type == 'business':
                    users = UserBusinessProfile.objects.filter()

                else:
                    users = Users.objects.filter()

                if email:
                    users = users.filter(email__iexact=email)
                if phone:
                    users = users.filter(phone_no=phone)

                if user_id:
                    if check_type == 'business':
                        users = users.exclude(user_id=user_id)
                    else:
                        users = users.exclude(id=user_id)
                if users.count() > 0:
                    exists = True
                else:
                    exists = False

                status = 201
                msg = 'Fetch data'
                all_data = {
                    'exists': exists
                }
            else:
                status = 403
                msg = 'Email or phone no is required'
            # if email or phone:
            #     if check_type == 'business':
            #         users = UserBusinessProfile.objects.filter()
            #         if email:
            #             users = users.filter(email__iexact=email)
            #         if phone:
            #             users = users.filter(phone_no=phone)
            #         if user_id:
            #             users = users.exclude(user_id=user_id)
            #         users = users.exclude(user__status__in=[5])
            #         if users.count() > 0:
            #             exists = True
            #         else:
            #             exists = False
            #
            #     elif check_type == 'main':
            #         users = Users.objects.filter()
            #         if email:
            #             users = users.filter(email__iexact=email)
            #         if phone:
            #             users = users.filter(phone_no=phone)
            #         if user_id:
            #             users = users.exclude(id=user_id)
            #
            #         users = users.exclude(status__in=[5])
            #         if users.count() > 0:
            #             exists = True
            #         else:
            #             exists = False
            #
            #     status = 201
            #     msg = 'Fetch data'
            #     all_data = {
            #         'exists': exists
            #     }
            # else:
            #     status = 403
            #     msg = 'Email or phone no is required'

            return Response(response.parsejson(msg, all_data, status=status))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetBusinessInfoApiView(APIView):
    """
    Get business info
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist", "", status=403))
                data['user'] = user_id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            user_business_profile = UserBusinessProfile.objects.filter(user=user_id).first()
            serializer = GetBusinessInfoSerializer(user_business_profile)
            return Response(response.parsejson("Fetch Data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateBusinessInfoApiView(APIView):
    """
    Update business info
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Network not exist", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))
                data['user'] = users.id
                user_id = users.id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "company_name" in data and data['company_name'] != "":
                company_name = data['company_name']
            else:
                return Response(response.parsejson("company_name is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                user_business_profile = UserBusinessProfile.objects.filter(phone_no=data['phone_no']).\
                    exclude(user=user_id).first()
                if user_business_profile:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "mobile_no" in data and data['mobile_no'] != "":
                user_business_profile = UserBusinessProfile.objects.filter(mobile_no=data['mobile_no']).\
                    exclude(user=user_id).first()
                if user_business_profile:
                    # Translators: This message appears when mobile no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))
            else:
                return Response(response.parsejson("mobile_no is required", "", status=403))

            if "email" in data and data['email'] != "":
                user_business_profile = UserBusinessProfile.objects.filter(email__iexact=data['email']).exclude(user=user_id).first()
                if user_business_profile:
                    # Translators: This message appears when email already in business db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(data['email'])
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("business_email is required", "", status=403))

            if "licence_no" in data and data['licence_no'] != "":
                licence_no = data['licence_no']
            else:
                return Response(response.parsejson("licence_no is required", "", status=403))

            # if "address_first" in data and data['address_first'] != "":
            #     address_first = data['address_first']
            # else:
            #     return Response(response.parsejson("address_first is required", "", status=403))
            #
            # if "state" in data and data['state'] != "":
            #     state = data['state']
            # else:
            #     return Response(response.parsejson("state is required", "", status=403))
            #
            # if "postal_code" in data and data['postal_code'] != "":
            #     postal_code = data['postal_code']
            # else:
            #     return Response(response.parsejson("postal_code is required", "", status=403))

            if "address" in data and len(data['address']) > 0:
                address = data['address']
            else:
                return Response(response.parsejson("address is required", "", status=403))

            if "country" in data and data['country'] != "":
                country = data['country']
            else:
                country = None
                # return Response(response.parsejson("country is required", "", status=403))

            user_business_profile = UserBusinessProfile.objects.filter(user=user_id).first()
            if user_business_profile is None:
                return Response(response.parsejson("Business info not found.", "", status=201))
            data['status'] = 1
            with transaction.atomic():
                serializer = UserBusinessProfileSerializer(user_business_profile, data=data)
                if serializer.is_valid():
                    serializer.save()
                    ProfileAddress.objects.filter(user=user_id, address_type=2).delete()
                    for row in address:
                        row['user'] = user_id
                        row['address_type'] = 2
                        row['status'] = 1
                        row['added_by'] = user_id
                        row['updated_by'] = user_id
                        serializer = ProfileAddressSerializer(data=row)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Business info updated Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChangePlanApiView(APIView):
    """
    Change Plan
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            amount = None
            order_id = None
            transaction_id = None

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            
            site_owner = Users.objects.filter(site=site_id).first()
            site_owner = site_owner.id
            user_subscription = UserSubscription.objects.filter(user=site_owner, subscription_status=1).first()
            exit_plan = int(user_subscription.payment_amount)
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))
                data['user'] = user_id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "opted_plan" in data and data['opted_plan'] != "":
                opted_plan = int(data['opted_plan'])
                plan_pricing = PlanPricing.objects.filter(subscription=opted_plan, is_active=1, plan_type__is_active=1).first()
                amount = plan_pricing.cost
                if plan_pricing is None:
                    return Response(response.parsejson("Plan not available.", "", status=403))
                data['opted_plan'] = plan_pricing.id
            else:
                return Response(response.parsejson("opted_plan is required", "", status=403))

            if "theme_id" in data and data['theme_id'] != "":
                theme_id = int(data['theme_id'])
                data['theme'] = theme_id
                theme = ThemesAvailable.objects.filter(id=theme_id, is_active=1).first()
                if theme is None:
                    return Response(response.parsejson("Theme not available", "", status=403))
            else:
                return Response(response.parsejson("theme_id is required", "", status=403))

            if "cc_ac_no" in data and data['cc_ac_no'] != "":
                cc_ac_no = data['cc_ac_no']
            else:
                return Response(response.parsejson("cc_ac_no is required", "", status=403))

            if "cc_ac_type_name" in data and data['cc_ac_type_name'] != "":
                cc_ac_type_name = data['cc_ac_type_name']
            else:
                return Response(response.parsejson("cc_ac_type_name is required", "", status=403))
            # plan_type = PlanType.objects.filter(id=plan_pricing.plan_type_id).first()
            data['start_date'] = timezone.now()
            data['end_date'] = timezone.now() + timezone.timedelta(days=plan_pricing.plan_type.duration_in_days)
            data['payment_amount'] = plan_pricing.cost
            data['payment_status'] = 1
            data['subscription_status'] = 1
            data['added_by'] = user_id
            data['updated_by'] = user_id
            plan_subscribed = UserSubscription.objects.filter(user=user_id, subscription_status=1).first()
            # ------Check plan------
            if plan_subscribed is not None and plan_subscribed.opted_plan.subscription.id == opted_plan:
                return Response(response.parsejson("You have same plan.", "", status=403))
            subscription_id = None
            if plan_subscribed is not None:
                subscription_id = plan_subscribed.id
            payment_data = {}
            payment_data['user'] = user_id
            payment_data['payment_type'] = 1
            payment_data['payment_amount'] = plan_pricing.cost
            payment_data['amount_paid'] = plan_pricing.cost
            payment_data['response_code'] = "done"
            payment_data['response_message'] = "success"
            payment_data['transaction_type'] = 1
            payment_data['subscription_status'] = 1
            payment_data['cc_ac_no'] = cc_ac_no
            payment_data['cc_ac_type_name'] = cc_ac_type_name
            payment_data['payment_mode'] = "Online"
            serializer = UserPaymentSerializer(data=payment_data)
            with transaction.atomic():
                if serializer.is_valid():
                    transaction_data = serializer.save()
                    transaction_id = transaction_data.id
                    if int(opted_plan) == 2:
                        data['is_free'] = 1
                    serializer = UserSubscriptionSerializer(data=data)
                    if serializer.is_valid():
                        subscription = serializer.save()
                        new_subscription_id = subscription.id
                        order_id = new_subscription_id
                        if subscription_id is not None:
                            UserSubscription.objects.filter(id=subscription_id).update(subscription_status=2)

                        # ----------Subscription Payment-----------
                        subscription_payment_data = {}
                        subscription_payment_data['subscription'] = new_subscription_id
                        subscription_payment_data['payment'] = transaction_id
                        serializer = SubscriptionPaymentSerializer(data=subscription_payment_data)
                        if serializer.is_valid():
                            serializer.save()
                            # -----------------Theme selection------------
                            user_theme = UserTheme.objects.filter(id=theme_id, status=1, domain=users.site_id).first()
                            if user_theme is None:
                                # -------------Inactive all theme for domain---------
                                try:
                                    UserTheme.objects.filter(status=1, domain=users.site_id).update(status=2)
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(exp, "", status=403))

                                user_theme_data = {}
                                user_theme_data['domain'] = users.site_id
                                user_theme_data['theme'] = theme_id
                                user_theme_data['status'] = 1
                                serializer = UserThemeSerializer(data=user_theme_data)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    copy_errors = serializer.errors.copy()
                                    return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))
                        # -----------------Permission----------------
                        try:
                            permission = None
                            if opted_plan == 2:
                                permission = LookupPermission.objects.filter(id__in=[5, 7], is_active=1).values("id")
                            elif opted_plan == 3:
                                permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).exclude(id=1).values("id")
                            elif opted_plan == 4:
                                permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).values("id")
                            if permission is not None:
                                UserPermission.objects.filter(domain=site_id, user=user_id).delete()
                                for permission_data in permission:
                                    user_permission = UserPermission()
                                    user_permission.domain_id = site_id
                                    user_permission.user_id = user_id
                                    user_permission.permission_id = permission_data['id']
                                    user_permission.is_permission = 1
                                    user_permission.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            all_data = {}
            all_data['amount'] = amount
            all_data['order_id'] = "IC-" + str(order_id) if order_id is not None else ""
            all_data['transaction_id'] = "000" + str(transaction_id) if transaction_id is not None else ""
            #-------------Email -------------
            plan_detail = SubscriptionPlan.objects.get(id=opted_plan)
            current_plan = int(plan_pricing.cost)
            if current_plan > exit_plan:
                template_data = {"domain_id": site_id, "slug": "upgrade_plan"}
            else:
                template_data = {"domain_id": site_id, "slug": "plan_downgrade"}
            extra_data = {'web_url': settings.FRONT_BASE_URL, 'plan_name': plan_detail.plan_name, 'plan_price': plan_pricing.cost, 'plan_description':plan_detail.plan_desc, "domain_id": site_id}
            compose_email(to_email=[users], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Plan updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanDashboardApiView(APIView):
    """
    Plan Dashboard
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))

                site_owner = Users.objects.filter(site=site_id).first()
                if site_owner is None:
                    return Response(response.parsejson("Site owner not exist.", "", status=403))
                site_owner = site_owner.id
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            if users.site_id is None:
                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1).first()
                if network_user is None:
                    return Response(response.parsejson("You are not agent/broker for this site.", "", status=403))
            user_subscription = UserSubscription.objects.filter(user=site_owner, subscription_status=1).last()
            serializer = PlanDashboardSerializer(user_subscription)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanBillingHistoryApiView(APIView):
    """
    Plan billing history
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            user_subscription = UserSubscription.objects.filter(user__site=site_id)
            total = user_subscription.count()
            user_subscription = user_subscription.order_by("-id").only("id")[offset: limit]
            serializer = PlanBillingHistorySerializer(user_subscription, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckSubdomainApiView(APIView):
    """
    Check subdomain
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip()
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            network_domain = NetworkDomain.objects.filter(domain_name=domain_name, is_active=1).first()
            all_data = {"domain_name": False}
            if network_domain is not None:
                all_data["domain_name"] = True
                all_data["site_id"] = network_domain.id
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SettingsDataApiView(APIView):
    """
    Settings Data
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip()
                network = NetworkDomain.objects.filter(domain_name=domain_name, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                site_id = network.id
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif users.site_id != site_id:
                    network_user = NetworkUser.objects.filter(user=user_id, domain=site_id, status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not registered for this domain.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            users = Users.objects.filter(id=user_id, status=1).first()
            serializer = SettingsDataSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserListingApiView(APIView):
    """
    Admin User listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            user = None
            if 'user' in data and data['user'] != "":
                user = data['user'].lower()

            users = Users.objects.exclude(user_type=3).exclude(status_id=5)
            if user is not None and user == "broker":
                users = users.filter(site__isnull=False)
            elif user is not None and user == "agent":
                # users = users.filter(site__isnull=True, network_user__is_agent=1)
                users = users.filter(site__isnull=True)
            # -------Filter-------
            if "user_type" in data and data['user_type'] != "":
                users = users.filter(user_type=data['user_type'])
            
            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                users = users.filter(status__in=data['status'])
            
            if "site" in data and type(data['site']) == list and len(data['site']) > 0:
                users = users.filter(site__in=data['site'])

            if "subscription" in data and type(data['subscription']) == list and len(data['subscription']) == 1:
                if int(data['subscription'][0]) == 1:
                    users = users.filter(stripe_customer_id__isnull=False, stripe_subscription_id__isnull=False)
                elif int(data['subscription'][0]) == 2:
                    users = users.filter(stripe_customer_id__isnull=True, stripe_subscription_id__isnull=True)

            if "agent_type" in data and type(data['agent_type']) == list and len(data['agent_type']) > 0:
                if 'agent' in data['agent_type'] and len(data['agent_type']) == 1:
                    users = users.filter(site__isnull=True)
                if 'broker' in data['agent_type'] and len(data['agent_type']) == 1:
                    users = users.filter(site__isnull=False)
            
            if "plan_type" in data and type(data['plan_type']) == list and len(data['plan_type']) > 0:
                users = users.filter(
                    user_subscription__opted_plan__subscription__in=data['plan_type'],
                    user_subscription__payment_status=1,
                    user_subscription__subscription_status=1
                ).distinct()
            
            
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    users = users.filter(Q(id=search) | Q(phone_no__icontains=search) | Q(site__domain_name__icontains=search) | Q(user_business_profile__licence_no__icontains=search))
                else:
                    users = users.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(email__icontains=search) | Q(first_name__icontains=search) |
                                         Q(last_name__icontains=search) | Q(user_type__user_type__icontains=search) |
                                         Q(site__domain_name__icontains=search) | Q(site__domain_url__icontains=search) | Q(full_name__icontains=search) | Q(user_business_profile__licence_no__icontains=search) | Q(phone_no__icontains=search))
                if not search.isdigit() and int(data['user_type']) == 1:
                    users = users.filter(Q(network_user__domain__domain_name__icontains=search))

            total = users.count()
            users = users.order_by("-id").only("id")[offset:limit]
            serializer = AdminUserListingSerializer(users, many=True)
            all_data = {
                'data': serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserChangeStatusApiView(APIView):
    """
    Admin User Change Status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
                if int(status) == 1:
                    template_data = {"domain_id": "", "slug": "account_activated"}
                else:
                    template_data = {"domain_id": "", "slug": "account_de-activation"}
            else:
                return Response(response.parsejson("status is required", "", status=403))

            Users.objects.filter(id=user_id).update(status=status)
            #send Email=======================
            user_data = Users.objects.get(id=user_id)
            user_name = user_data.first_name if user_data.first_name is not None else ""
            user_email = user_data.email if user_data.email is not None else ""
            super_data = Users.objects.get(user_type = 3)
            super_name = super_data.first_name if super_data.first_name is not None else ""
            super_email = super_data.email if super_data.email is not None else ""
            extra_data = {
                'user_name': user_name,
                'account_email': user_email,
                'name': super_name,
                'email': super_email,
            }
            compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetSiteDetailApiView(APIView):
    """
    Get Site Detail
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip().lower()
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            network_domain = NetworkDomain.objects.get(domain_name=domain_name, is_active=1)
            serializer = GetSiteDetailSerializer(network_domain)
            all_data = {"data": serializer.data}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NewGetSiteDetailApiView(APIView):
    """
    New Get Site Detail
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip().lower()
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            domain_name = "https://"+domain_name
            network_domain = NetworkDomain.objects.get(domain_url=domain_name, is_active=1, is_delete=False)
            serializer = GetSiteDetailSerializer(network_domain)
            all_data = {"data": serializer.data}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserRegistrationApiView(APIView):
    """
    Admin User Registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            user_type_name = 'Buyer/Seller'
            login_domain = settings.SUBDOMAIN_URL
            login_url = login_domain.replace("###", 'reba')
            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = int(data['added_by'])
                users = Users.objects.filter(id=added_by, user_type=3, status=1).first()
                if users is None:
                    # Translators: This message appears when user not exist.
                    return Response(response.parsejson("Added by user not exist.", "", status=403))
            else:
                return Response(response.parsejson("added_by is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                users = Users.objects.filter(phone_no=phone_no).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if phone_no:
                hashed_pwd = make_password(str(phone_no))
                data['password'] = hashed_pwd
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            data['encrypted_password'] = b64encode(str(phone_no))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            address = None
            if "address" in data and len(data['address']) > 0:
                address = data['address']

            # -------------Check Data for Agent/Broker Only----------------
            if user_type == 2:
                user_type_name = 'Agent/Broker'
                business_data = {}
                if "business_first_name" in data and data['business_first_name'] != "":
                    business_data['first_name'] = data['business_first_name']
                else:
                    return Response(response.parsejson("business_first_name is required", "", status=403))

                if "business_last_name" in data and data['business_last_name'] != "":
                    business_data['last_name'] = data['business_last_name']
                else:
                    return Response(response.parsejson("business_last_name is required", "", status=403))

                if "company_name" in data and data['company_name'] != "":
                    company_name = data['company_name']
                    business_data['company_name'] = data['company_name']
                else:
                    return Response(response.parsejson("company_name is required", "", status=403))

                if "business_phone_no" in data and data['business_phone_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(phone_no=data['business_phone_no']).first()
                    if user_business_profile:
                        # Translators: This message appears when phone no already in db
                        return Response(response.parsejson("Business Phone no already exist", "", status=403))
                    business_data['phone_no'] = data['business_phone_no']
                else:
                    return Response(response.parsejson("business_phone_no is required", "", status=403))

                if "business_mobile_no" in data and data['business_mobile_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(mobile_no=data['business_mobile_no']).first()
                    if user_business_profile:
                        # Translators: This message appears when mobile no already in db
                        return Response(response.parsejson("Business Mobile no already exist", "", status=403))
                    business_data['mobile_no'] = data['business_mobile_no']
                else:
                    return Response(response.parsejson("business_mobile_no is required", "", status=403))

                if "business_email" in data and data['business_email'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(email=data['business_email']).first()
                    if user_business_profile:
                        # Translators: This message appears when email already in business db
                        return Response(response.parsejson("Business Email already exist", "", status=403))
                    try:
                        validate_email(data['business_email'])
                    except ValidationError:
                        # Translators: This message appears when email is invalid
                        return Response(response.parsejson("Invalid business email address", "", status=404))
                    business_data['email'] = data['business_email']
                else:
                    return Response(response.parsejson("business_email is required", "", status=403))

                if "licence_no" in data and data['licence_no'] != "":
                    business_data['licence_no'] = data['licence_no']
                else:
                    return Response(response.parsejson("licence_no is required", "", status=403))

                # if "address_first" in data and data['address_first'] != "":
                #     # business_data['address_first'] = data['address_first']
                #     address_first = data['address_first']
                # else:
                #     return Response(response.parsejson("address_first is required", "", status=403))
                #
                # if "state" in data and data['state'] != "":
                #     # business_data['state'] = data['state']
                #     state = data['state']
                # else:
                #     return Response(response.parsejson("state is required", "", status=403))
                #
                # if "postal_code" in data and data['postal_code'] != "":
                #     # business_data['postal_code'] = data['postal_code']
                #     postal_code = data['postal_code']
                # else:
                #     return Response(response.parsejson("postal_code is required", "", status=403))

                business_data['company_logo'] = None
                if "company_logo" in data and data['company_logo'] != "":
                    business_data['company_logo'] = int(data['company_logo'])

                if "subscription_id" in data and data['subscription_id'] != "":
                    subscription_id = int(data['subscription_id'])
                    subscription = SubscriptionPlan.objects.filter(id=subscription_id, is_active=1).first()
                    if subscription is None:
                        return Response(response.parsejson("Plan not exist.", "", status=403))
                else:
                    return Response(response.parsejson("subscription_id is required", "", status=403))

                if "theme_id" in data and data['theme_id'] != "":
                    theme_id = int(data['theme_id'])
                    theme = ThemesAvailable.objects.filter(id=theme_id, is_active=1).first()
                    if theme is None:
                        return Response(response.parsejson("Theme not exist", "", status=403))
                else:
                    return Response(response.parsejson("theme_id is required", "", status=403))
            with transaction.atomic():
                serializer = UsersSerializer(data=data)
                # -----------------------Activate token----------------------
                activate_token = forgot_token()
                if not activate_token:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))
                
                if serializer.is_valid():
                    serializer.validated_data['status_id'] = 1
                    serializer.validated_data['activation_code'] = activate_token
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))

                    # -----------------Save profile address--------------
                    if address is not None:
                        for row in address:
                            row['user'] = user_id
                            row['address_type'] = user_type
                            row['status'] = 1
                            row['added_by'] = user_id
                            row['updated_by'] = user_id
                            serializer = ProfileAddressSerializer(data=row)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                    # ------------Save Business Information-----------
                    if user_type == 2 and user_id > 0:
                        business_data['user'] = user_id
                        business_data['status'] = 1
                        serializer = UserBusinessProfileSerializer(data=business_data)
                        if serializer.is_valid():
                            serializer.validated_data['status_id'] = 1
                            serializer.save()

                            # ---------------Save Domain Network-----------
                            network_data = {}
                            subdomain_url = settings.SUBDOMAIN_URL
                            domain_name = make_subdomain(company_name)
                            domain_url = subdomain_url.replace("###", domain_name)
                            network_data['domain_type'] = 2
                            network_data['domain_name'] = domain_name
                            network_data['domain_url'] = domain_url
                            network_data['is_active'] = 1
                            serializer = NetworkDomainSerializer(data=network_data)
                            login_url = domain_url
                            if serializer.is_valid():
                                network = serializer.save()
                                network_id = network.id

                                # ------------------User Subscription plan updated-------------
                                user_subscription_data = {}
                                plan_pricing = PlanPricing.objects.filter(subscription=subscription_id).first()
                                if plan_pricing is None:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson("Subscription plan not exist.", "", status=403))
                                default_theme = ThemesAvailable.objects.filter(id=theme_id, is_active=1).first()
                                user_subscription_data['theme'] = None
                                if default_theme is not None:
                                    user_subscription_data['theme'] = default_theme.id
                                user_subscription_data['domain'] = network_id
                                user_subscription_data['user'] = user_id
                                user_subscription_data['opted_plan'] = plan_pricing.id
                                user_subscription_data['is_free'] = 1
                                user_subscription_data['payment_amount'] = plan_pricing.cost
                                user_subscription_data['payment_status'] = 1
                                user_subscription_data['subscription_status'] = 1
                                user_subscription_data['added_by'] = added_by
                                serializer = UserSubscriptionSerializer(data=user_subscription_data)
                                if serializer.is_valid():
                                    serializer.save()
                                    if default_theme is not None:
                                        user_theme_data = {}
                                        user_theme_data['domain'] = network_id
                                        user_theme_data['theme'] = default_theme.id
                                        user_theme_data['status'] = 1
                                        serializer = UserThemeSerializer(data=user_theme_data)
                                        if serializer.is_valid():
                                            serializer.save()
                                        else:
                                            transaction.set_rollback(True)  # -----Rollback Transaction----
                                            copy_errors = serializer.errors.copy()
                                            return Response(response.parsejson(copy_errors, "", status=403))

                                else:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    copy_errors = serializer.errors.copy()
                                    return Response(response.parsejson(copy_errors, "", status=403))

                                # -----------------Permission----------------
                                try:
                                    permission = None
                                    if subscription_id == 2:
                                        permission = LookupPermission.objects.filter(id__in=[5, 7], is_active=1).values("id")
                                    elif subscription_id == 3:
                                        permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).exclude(id=1).values("id")
                                    elif subscription_id == 4:
                                        permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).values("id")
                                    if permission is not None:
                                        UserPermission.objects.filter(domain=network_id, user=user_id).delete()
                                        for permission_data in permission:
                                            user_permission = UserPermission()
                                            user_permission.domain_id = network_id
                                            user_permission.user_id = user_id
                                            user_permission.permission_id = permission_data['id']
                                            user_permission.is_permission = 1
                                            user_permission.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))

                                try:
                                    # ------------Login Data------------
                                    users_data = Users.objects.filter(id=user_id).first()
                                    users_data.site_id = network_id  # ----Update User Table---
                                    users_data.save()
                                except Exception as exp:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(str(exp), exp, status=403))
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))

                        # -----------Set email template-------
                        try:
                            notification_template = NotificationTemplate.objects.filter(site__isnull=True, status=1)
                            if notification_template is not None:
                                for template in notification_template:
                                    new_template = NotificationTemplate()
                                    new_template.site_id = network_id
                                    new_template.event_id = template.event_id
                                    new_template.email_subject = template.email_subject
                                    new_template.email_content = template.email_content
                                    new_template.notification_text = template.notification_text
                                    new_template.push_notification_text = template.push_notification_text
                                    new_template.added_by_id = user_id
                                    new_template.updated_by_id = user_id
                                    new_template.status_id = 1
                                    new_template.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            # copy_errors.update(user_profile_serializer.errors)
                            return Response(response.parsejson(copy_errors, "", status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
            #==============Email Send=====================
            activation_link = settings.RESET_PASSWORD_URL + "/activation/?token=" + str(activate_token)
            template_data = {"domain_id": "", "slug": "welcome_user"}
            extra_data = {'user_name': first_name, 'email': email, 'password': phone_no, 'user_type': user_type_name, 'activation_link': activation_link, 'web_url': settings.FRONT_BASE_URL, 'domain_url': login_url}
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("User Registered Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserEditApiView(APIView):
    """
    Admin User Edit
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            site_id = None
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                site_data = NetworkDomain.objects.filter(id=site_id).first()
                if site_data is None:
                    return Response(response.parsejson("Network not available.", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = int(data['added_by'])
                users = Users.objects.filter(id=added_by, user_type=3, status=1).first()
                if users is None:
                    # Translators: This message appears when user not exist.
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("added_by is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user_data = Users.objects.filter(id=user_id).exclude(user_type=3).first()
                if user_data is None:
                    return Response(response.parsejson("User not found.", "", status=403))
                is_owner = None
                if user_data.site_id is not None and user_data.site_id > 0:
                    is_owner = True
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "user_type" in data and data['user_type'] != "":
                user_type = int(data['user_type'])
            else:
                return Response(response.parsejson("user_type is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                users = Users.objects.filter(phone_no=phone_no).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "address" in data and len(data['address']) > 0:
                address = data['address']
            else:
                return Response(response.parsejson("address is required.", "", status=403))
            # -------------Check Data for Agent/Broker Only----------------
            if user_type == 2:
                business_data = {}
                if "business_first_name" in data and data['business_first_name'] != "":
                    business_data['first_name'] = data['business_first_name']
                else:
                    return Response(response.parsejson("business_first_name is required", "", status=403))

                if "business_last_name" in data and data['business_last_name'] != "":
                    business_data['last_name'] = data['business_last_name']
                else:
                    return Response(response.parsejson("business_last_name is required", "", status=403))

                if "company_name" in data and data['company_name'] != "":
                    company_name = data['company_name']
                    business_data['company_name'] = data['company_name']
                else:
                    return Response(response.parsejson("company_name is required", "", status=403))

                if "business_phone_no" in data and data['business_phone_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(phone_no=data['business_phone_no']).exclude(user__id=user_id).first()
                    if user_business_profile:
                        # Translators: This message appears when phone no already in db
                        return Response(response.parsejson("Business Phone no already exist", "", status=403))
                    business_data['phone_no'] = data['business_phone_no']
                else:
                    return Response(response.parsejson("business_phone_no is required", "", status=403))

                if "business_mobile_no" in data and data['business_mobile_no'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(mobile_no=data['business_mobile_no']).exclude(user__id=user_id).first()
                    if user_business_profile:
                        # Translators: This message appears when mobile no already in db
                        return Response(response.parsejson("Business Mobile no already exist", "", status=403))
                    business_data['mobile_no'] = data['business_mobile_no']
                else:
                    return Response(response.parsejson("business_mobile_no is required", "", status=403))

                if "business_email" in data and data['business_email'] != "":
                    user_business_profile = UserBusinessProfile.objects.filter(email=data['business_email']).exclude(user__id=user_id).first()
                    if user_business_profile:
                        # Translators: This message appears when email already in business db
                        return Response(response.parsejson("Business Email already exist", "", status=403))
                    try:
                        validate_email(data['business_email'])
                    except ValidationError:
                        # Translators: This message appears when email is invalid
                        return Response(response.parsejson("Invalid business email address", "", status=404))
                    business_data['email'] = data['business_email']
                else:
                    return Response(response.parsejson("business_email is required", "", status=403))

                if "licence_no" in data and data['licence_no'] != "":
                    business_data['licence_no'] = data['licence_no']
                else:
                    return Response(response.parsejson("licence_no is required", "", status=403))

                # if "address_first" in data and data['address_first'] != "":
                #     business_data['address_first'] = data['address_first']
                # else:
                #     return Response(response.parsejson("address_first is required", "", status=403))

                # if "state" in data and data['state'] != "":
                #     business_data['state'] = data['state']
                # else:
                #     return Response(response.parsejson("state is required", "", status=403))

                # if "postal_code" in data and data['postal_code'] != "":
                #     business_data['postal_code'] = data['postal_code']
                # else:
                #     return Response(response.parsejson("postal_code is required", "", status=403))

                business_data['company_logo'] = None
                if "company_logo" in data and data['company_logo'] != "":
                    business_data['company_logo'] = int(data['company_logo'])
                if is_owner is not None:
                    if "domain_name" in data and data['domain_name'] != "":
                        domain_name = data['domain_name'].strip().lower()
                        network = NetworkDomain.objects.filter(domain_name=domain_name).exclude(id=site_id).first()
                        if network:
                            return Response(response.parsejson("Domain name already taken", "", status=403))
                    else:
                        return Response(response.parsejson("domain_name is required.", "", status=403))

                    if "domain_url" in data and data['domain_url'] != "":
                        domain_url = data['domain_url'].strip()
                        network = NetworkDomain.objects.filter(domain_url=domain_url).exclude(id=site_id).first()
                        if network:
                            return Response(response.parsejson("Domain url already taken", "", status=403))
                    else:
                        return Response(response.parsejson("domain_url is required", "", status=403))

                    if "subscription_id" in data and data['subscription_id'] != "":
                        subscription_id = int(data['subscription_id'])
                        subscription = SubscriptionPlan.objects.filter(id=subscription_id, is_active=1).first()
                        if subscription is None:
                            return Response(response.parsejson("Plan not exist.", "", status=403))
                    else:
                        return Response(response.parsejson("subscription_id is required", "", status=403))

                    if "theme_id" in data and data['theme_id'] != "":
                        theme_id = int(data['theme_id'])
                        theme = ThemesAvailable.objects.filter(id=theme_id, is_active=1).first()
                        if theme is None:
                            return Response(response.parsejson("Theme not exist", "", status=403))
                    else:
                        return Response(response.parsejson("theme_id is required", "", status=403))

            with transaction.atomic():
                serializer = UsersSerializer(user_data, data=data)
                if serializer.is_valid():
                    # serializer.validated_data['status_id'] = 1
                    users = serializer.save()
                    user_id = users.id
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
                # -----------------Save profile address--------------
                ProfileAddress.objects.filter(user=user_id, address_type=user_type).delete()
                for row in address:
                    row['user'] = user_id
                    row['address_type'] = user_type
                    row['status'] = 1
                    row['added_by'] = user_id
                    row['updated_by'] = user_id
                    serializer = ProfileAddressSerializer(data=row)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                if user_type == 2:
                    # ------------Save Business Information-----------
                    business_data['user'] = user_id
                    business_data['status'] = 1
                    business = UserBusinessProfile.objects.filter(user__id=user_id).first()
                    serializer = UserBusinessProfileSerializer(business, data=business_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        # copy_errors.update(user_profile_serializer.errors)
                        return Response(response.parsejson(copy_errors, "", status=403))
                    if is_owner is not None:
                        # ---------------Save Domain Network-----------
                        network_data = {}
                        subdomain_url = settings.SUBDOMAIN_URL
                        domain_url = subdomain_url.replace("###", domain_name)
                        network_data['domain_type'] = 2
                        network_data['domain_name'] = domain_name
                        network_data['domain_url'] = domain_url
                        network_data['is_active'] = 1
                        network = NetworkDomain.objects.filter(id=site_id).first()
                        serializer = NetworkDomainSerializer(network, data=network_data)
                        if serializer.is_valid():
                            network = serializer.save()
                            network_id = network.id
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                        # ------------------User Subscription plan updated-------------
                        user_subscription_data = {}
                        plan_pricing = PlanPricing.objects.filter(subscription=subscription_id).first()
                        if plan_pricing is None:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson("Subscription plan not exist.", "", status=403))
                        check_subscription = UserSubscription.objects.filter(user=user_id,
                                                                             opted_plan=plan_pricing.id,
                                                                             subscription_status=1).first()
                        if check_subscription is None:
                            # --------------Update User Subscription-----------
                            UserSubscription.objects.filter(user=user_id, subscription_status=1).update(
                                subscription_status=2)
                            user_subscription_data['domain'] = network_id
                            user_subscription_data['user'] = user_id
                            user_subscription_data['opted_plan'] = plan_pricing.id
                            user_subscription_data['is_free'] = 1 if plan_pricing.cost <= 0 else 0
                            user_subscription_data['payment_amount'] = plan_pricing.cost
                            user_subscription_data['payment_status'] = 1
                            user_subscription_data['subscription_status'] = 1
                            user_subscription_data['added_by'] = added_by
                            serializer = UserSubscriptionSerializer(data=user_subscription_data)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                copy_errors = serializer.errors.copy()
                                return Response(response.parsejson(copy_errors, "", status=403))

                        default_theme = ThemesAvailable.objects.filter(id=theme_id, is_active=1).first()
                        if default_theme is not None:
                            theme_check = UserTheme.objects.filter(domain=site_id, theme=theme_id,
                                                                   status=1).first()
                            if theme_check is None:
                                # -----------------Update user theme--------------
                                UserTheme.objects.filter(domain=site_id, status=1).update(status=2)

                                user_theme_data = {}
                                user_theme_data['domain'] = network_id
                                user_theme_data['theme'] = default_theme.id
                                user_theme_data['status'] = 1
                                serializer = UserThemeSerializer(data=user_theme_data)
                                if serializer.is_valid():
                                    serializer.save()
                                else:
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    copy_errors = serializer.errors.copy()
                                    return Response(response.parsejson(copy_errors, "", status=403))

                        try:
                            # ------------User Update------------
                            users_data = Users.objects.filter(id=user_id).first()
                            users_data.site_id = network_id  # ----Update User Table---
                            users_data.save()
                        except Exception as exp:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("User Updated Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserDetailApiView(APIView):
    """
    Admin user detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            user = Users.objects.get(id=user_id)
            serializer = AdminUserDetailSerializer(user)
            all_data = {"data": serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))

        except Exception as exp:
            return Response(response.parsejson(str(exp), "", status=403))


class AddNetworkUserApiView(APIView):
    """
    Add Network User
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user is not None and user.site_id == site_id:
                    return Response(response.parsejson("User is owner.", "", status=403))
                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is not None:
                    return Response(response.parsejson("Already exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            network_user = NetworkUser()
            network_user.domain_id = site_id
            network_user.user_id = user_id
            network_user.status_id = 1
            network_user.save()
            return Response(response.parsejson("User added in to site successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MakeAgentApiView(APIView):
    """
    Make agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, network_user__user=user_id, network_user__domain=site_id).first()
                if users is None:
                    # Translators: This message appears when user not exist
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif users.site_id == site_id:
                    # Translators: This message appears when make broker as a agent
                    return Response(response.parsejson("You are broker.", "", status=403))

            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                users = Users.objects.filter(Q(phone_no=phone_no) | Q(user_business_profile__phone_no=phone_no)).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            mobile_no = None
            if "mobile_no" in data and data['mobile_no'] != "":
                mobile_no = int(data['mobile_no'])
                users = Users.objects.filter(Q(user_business_profile__mobile_no=mobile_no)).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(Q(email__iexact=email) | Q(user_business_profile__email__iexact=email)).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "company_name" in data and data['company_name'] != "":
                company_name = data['company_name']
            else:
                return Response(response.parsejson("company_name is required", "", status=403))

            if "licence_no" in data and data['licence_no'] != "":
                licence_no = data['licence_no']
            else:
                licence_no = None

            if "address_first" in data and data['address_first'] != "":
                address_first = data['address_first']
            else:
                return Response(response.parsejson("address_first is required", "", status=403))

            if "state" in data and data['state'] != "":
                state = int(data['state'])
            else:
                return Response(response.parsejson("state is required", "", status=403))

            if "postal_code" in data and data['postal_code'] != "":
                postal_code = data['postal_code']
            else:
                return Response(response.parsejson("postal_code is required", "", status=403))

            if "permission" in data and len(data['permission']) > 0:
                permission = data['permission']
            else:
                return Response(response.parsejson("permission is required", "", status=403))

            company_logo = None
            if "company_logo" in data and data['company_logo'] != "":
                company_logo = int(data['company_logo'])

            with transaction.atomic():
                try:
                    # --------------User--------------
                    users = Users.objects.get(id=user_id)
                    users.user_type_id = 2
                    users.save()

                    user_business_profile = UserBusinessProfile.objects.filter(user=user_id, status=1).first()
                    if user_business_profile is None:
                        user_business_profile = UserBusinessProfile()
                        user_business_profile.user_id = user_id
                        user_business_profile.status_id = 1
                    user_business_profile.first_name = first_name
                    user_business_profile.last_name = last_name
                    user_business_profile.phone_no = phone_no
                    user_business_profile.email = email
                    user_business_profile.company_name = company_name
                    user_business_profile.licence_no = licence_no
                    # user_business_profile.address_first = address_first
                    # user_business_profile.state_id = state
                    # user_business_profile.postal_code = postal_code
                    user_business_profile.company_logo = company_logo
                    user_business_profile.save()

                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                    network_user.is_agent = 1
                    network_user.agent_added_on = timezone.now()
                    network_user.is_upgrade = 1
                    network_user.save()

                    # ---------------Profile address------------
                    profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                            "state": state, "postal_code": postal_code, "status": 1,
                                            "added_by": user_id, "updated_by": user_id}
                    ProfileAddress.objects.filter(user=user_id, address_type=2).delete()
                    serializer = ProfileAddressSerializer(data=profile_address_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        # copy_errors.update(user_profile_serializer.errors)
                        return Response(response.parsejson(copy_errors, "", status=403))

                    # -----------------Permission----------------
                    UserPermission.objects.filter(user=user_id, domain=site_id).delete()
                    for permission_data in permission:
                        user_permission = UserPermission()
                        user_permission.domain_id = site_id
                        user_permission.user_id = user_id
                        user_permission.permission_id = permission_data['permission_id']
                        user_permission.is_permission = permission_data['is_permission']
                        user_permission.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            # ------------------------Email-----------------------
            domain_name = network.domain_name
            subdomain_url = settings.SUBDOMAIN_URL
            dashboard_link = subdomain_url.replace("###", domain_name)+"admin/agents/"
            extra_data = {"user_name": first_name, "domain_id": site_id, "domain_name": domain_name, "dashboard_link": dashboard_link}
            template_data = {"domain_id": site_id, "slug": "upgrade_agent"}
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            #=============send email to broker======================
            broker_detail = Users.objects.get(site_id=site_id)
            broker_name = broker_detail.first_name
            broker_email =  broker_detail.email
            dashboard_link = subdomain_url.replace("###", domain_name)+"admin/agents/"
            template_data = {"domain_id": site_id, "slug": "upgrade_agent_broker"}
            extra_data = {"user_name": broker_name, "domain_id": site_id, "domain_name": domain_name, 'name': first_name, 'user_phone': phone_format(phone_no), 'user_email': email, 'dashboard_link': dashboard_link}
            compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            # add notif to agent
            try:
                add_notification(
                    site_id,
                    title="Agent Upgrade",
                    content="Congratulations! You are now " + network.domain_name + " agent!",
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=2,
                    notification_type=3
                )
            except Exception as e:
                print(e)
                pass
            return Response(response.parsejson("Upgrade to agent successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MakeAgentDetailApiView(APIView):
    """
    Make Agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))

                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is None:
                    return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            users = Users.objects.get(id=user_id)
            serializer = MakeAgentDetailSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserListingApiView(APIView):
    """
    Subdomain User Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            users = Users.objects.filter(network_user__domain=site_id, network_user__is_agent=0, network_user__status=1)
            # ----------------Filter---------------
            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                users = users.filter(status__in=data['status'])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = str(data['search'])
                if search.isdigit():
                    users = users.filter(Q(id=search) | Q(phone_no=search))
                else:
                    users = users.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(email__icontains=search) | Q(phone_no__icontains=search) | Q(full_name__icontains=search))
            total = users.count()
            users = users.order_by("-id").only('id')[offset:limit]
            serializer = SubdomainUserListingSerializer(users, many=True, context=site_id)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetPersonalInfoApiView(APIView):
    """
    Get Personal Info
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User Not Exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            users = Users.objects.get(id=user_id, status=1)
            serializer = GetPersonalInfoSerializer(users)
            return Response(response.parsejson("Fetch Data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdatePersonalInfoApiView(APIView):
    """
    Update Personal Info
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User Not Exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = data['phone_no']
                users = Users.objects.filter(phone_no=phone_no).exclude(id=user_id).first()
                if users is not None:
                    return Response(response.parsejson("Phone no already exist.", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).exclude(id=user_id).first()
                if users is not None:
                    return Response(response.parsejson("Email already exist.", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            upload_id = None
            if "upload_id" in data and data['upload_id'] != "":
                upload_id = data['upload_id']

            Users.objects.filter(id=user_id).update(first_name=first_name, last_name=last_name, phone_no=phone_no, email=email, profile_image=upload_id)
            return Response(response.parsejson("Personal info updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CreateAgentApiView(APIView):
    """
    Create agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            data['user_type'] = 2
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(Q(email__iexact=email) | Q(user_business_profile__email__iexact=email)).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                # users = Users.objects.filter(Q(phone_no=phone_no) | Q(user_business_profile__phone_no=phone_no)).first()
                # if users:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            mobile_no = None
            if "mobile_no" in data and data['mobile_no'] != "":
                mobile_no = int(data['mobile_no'])
                users = Users.objects.filter(Q(user_business_profile__mobile_no=mobile_no)).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))
            # else:
            #     data['mobile_no'] = None
                # return Response(response.parsejson("phone_no is required", "", status=403))

            if phone_no:
                hashed_pwd = make_password(str(phone_no))
                data['password'] = hashed_pwd
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))
            # --------This for authentication--------
            data['encrypted_password'] = b64encode(str(phone_no))

            if "company_name" in data and data['company_name'] != "":
                company_name = data['company_name']
            else:
                return Response(response.parsejson("company_name is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "address_first" in data and data['address_first'] != "":
                address_first = data['address_first']
            else:
                return Response(response.parsejson("address_first is required", "", status=403))

            if "state" in data and data['state'] != "":
                state = data['state']
            else:
                return Response(response.parsejson("state is required", "", status=403))

            if "postal_code" in data and data['postal_code'] != "":
                postal_code = data['postal_code']
            else:
                return Response(response.parsejson("postal_code is required", "", status=403))

            if "licence_no" in data and data['licence_no'] != "":
                licence_no = data['licence_no']
            else:
                licence_no = None

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required", "", status=403))

            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            company_logo = None
            if "company_logo" in data and data['company_logo'] != "":
                company_logo = int(data['company_logo'])

            if "permission" in data and len(data['permission']) > 0:
                permission = data['permission']
            else:
                return Response(response.parsejson("permission is required", "", status=403))

            with transaction.atomic():
                # --------------User--------------
                data['status'] = 1
                data['activation_date'] = timezone.now()
                # ---------------------Activation token----------------
                activation_code = forgot_token()
                if not activation_code:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))
                data['activation_code'] = activation_code
                serializer = UsersSerializer(data=data)
                if serializer.is_valid():
                    serializer.validated_data['status_id'] = 1
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # -------------Business profile-----------
                # business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                #                  "first_name": first_name, "last_name": last_name, "address_first": address_first,
                #                  "state": state, "postal_code": postal_code, "licence_no": licence_no, "status": 1,
                #                  "company_logo": company_logo, "mobile_no": mobile_no}
                business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                                 "first_name": first_name, "last_name": last_name, "licence_no": licence_no, "status": 1,
                                 "company_logo": company_logo, "mobile_no": mobile_no}

                serializer = UserBusinessProfileSerializer(data=business_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # ---------------Profile address------------
                profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                        "state": state, "postal_code": postal_code, "status": 1, "added_by": user_id,
                                        "updated_by": user_id}
                serializer = ProfileAddressSerializer(data=profile_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                profile_home_address_data = {"user": user_id, "address_type": 1, "address_first": address_first,
                                             "state": state, "postal_code": postal_code, "status": 1,
                                             "added_by": user_id,
                                             "updated_by": user_id}
                serializer = ProfileAddressSerializer(data=profile_home_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # -------------User network------------
                user_network = {"domain": site_id, "user": user_id, "is_agent": 1, "status": status,
                                "agent_added_on": timezone.now()}
                serializer = NetworkUserSerializer(data=user_network)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    # -----------------Permission----------------
                    UserPermission.objects.filter(user=user_id, domain=site_id).delete()
                    for permission_data in permission:
                        user_permission = UserPermission()
                        user_permission.domain_id = site_id
                        user_permission.user_id = user_id
                        user_permission.permission_id = permission_data['permission_id']
                        user_permission.is_permission = permission_data['is_permission']
                        user_permission.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            # ------------------------Email-----------------------
            #extra_data = {"user_name": first_name, "email": email, "password": phone_no}
            template_data = {"domain_id": site_id, "slug": "agent_added"}
            #activation_link = settings.RESET_PASSWORD_URL + "/activation/?token=" + str(activation_code)
            #user_image_link = None
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            user_image_link = None
            broker_detail = Users.objects.get(site_id=site_id)
            broker_name = broker_detail.first_name
            broker_email = broker_detail.email
            if "profile_image" in data and data['profile_image'] != "":
                user_details = Users.objects.get(id=user_id)
                upload = UserUploads.objects.get(id=int(user_details.profile_image))
                bucket_name = upload.bucket_name
                image = upload.doc_file_name
                user_image_link = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
            domain_url = subdomain_url.replace("###", domain_name)+"edit-profile"
            domain_name_url = subdomain_url.replace("###", domain_name)
            extra_data = {"user_name": first_name, "user_image_link": user_image_link, "web_url": settings.FRONT_BASE_URL, "user_address": address_first, "user_company": company_name, "user_license_no": licence_no, "user_phone": phone_format(phone_no), "user_email": email, "dashboard_link": domain_url, "domain_id": site_id, 'domain_name': domain_name_url, 'password': phone_no, 'name': first_name}
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            #=============send broker==============
            template_data = {"domain_id": site_id, "slug": "agent_added_broker"}
            domain_url = subdomain_url.replace("###", domain_name)+"admin/agents/"
            extra_data = {"user_name": broker_name, "user_image_link": user_image_link, "web_url": settings.FRONT_BASE_URL, "user_address": address_first, "user_company": company_name, "user_license_no": licence_no, "user_phone": phone_format(phone_no), "user_email": email, "dashboard_link": domain_url, "domain_id": site_id, 'domain_name': domain_name_url, 'password': phone_no, 'name': first_name}
            compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            
            # add notif to agent
            try:
                add_notification(
                    site_id,
                    title="Create Agent",
                    content="Welcome! You are now " + domain_name + " agent!",
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=2,
                    notification_type=3
                )
            except Exception as e:
                print(e)
                pass
            return Response(response.parsejson("Agent Created Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CreateSubAdminApiView(APIView):
    """
    Create Sub Admin
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            data['user_type'] = 4
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(Q(email__iexact=email) | Q(user_business_profile__email__iexact=email)).first()
                if users:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                # users = Users.objects.filter(Q(phone_no=phone_no) | Q(user_business_profile__phone_no=phone_no)).first()
                # if users:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            mobile_no = None
            if "mobile_no" in data and data['mobile_no'] != "":
                mobile_no = int(data['mobile_no'])
                users = Users.objects.filter(Q(user_business_profile__mobile_no=mobile_no)).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))
            # else:
            #     data['mobile_no'] = None
                # return Response(response.parsejson("phone_no is required", "", status=403))

            if phone_no:
                hashed_pwd = make_password(str(phone_no))
                data['password'] = hashed_pwd
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))
            # --------This for authentication--------
            data['encrypted_password'] = b64encode(str(phone_no))

            # if "company_name" in data and data['company_name'] != "":
            #     company_name = data['company_name']
            # else:
            #     return Response(response.parsejson("company_name is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "address_first" in data and data['address_first'] != "":
                address_first = data['address_first']
            else:
                return Response(response.parsejson("address_first is required", "", status=403))

            if "state" in data and data['state'] != "":
                state = data['state']
            else:
                return Response(response.parsejson("state is required", "", status=403))

            if "postal_code" in data and data['postal_code'] != "":
                postal_code = data['postal_code']
            else:
                return Response(response.parsejson("postal_code is required", "", status=403))

            # if "licence_no" in data and data['licence_no'] != "":
            #     licence_no = data['licence_no']
            # else:
            #     licence_no = None

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required", "", status=403))

            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            # company_logo = None
            # if "company_logo" in data and data['company_logo'] != "":
            #     company_logo = int(data['company_logo'])

            if "permission" in data and len(data['permission']) > 0:
                permission = data['permission']
            else:
                return Response(response.parsejson("permission is required", "", status=403))

            with transaction.atomic():
                # --------------User--------------
                data['status'] = 1
                data['activation_date'] = timezone.now()
                # ---------------------Activation token----------------
                activation_code = forgot_token()
                if not activation_code:
                    return Response(response.parsejson("Getting Some Issue.", "", status=403))
                data['activation_code'] = activation_code
                serializer = UsersSerializer(data=data)
                if serializer.is_valid():
                    serializer.validated_data['status_id'] = 1
                    users = serializer.save()
                    user_id = users.id
                    # ----------Create application for user-------
                    application = create_application(user_id)
                    if not application:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson("Application not created.", "", status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
                
                # business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                #                  "first_name": first_name, "last_name": last_name, "licence_no": licence_no, "status": 1,
                #                  "company_logo": company_logo, "mobile_no": mobile_no}

                # serializer = UserBusinessProfileSerializer(data=business_data)
                # if serializer.is_valid():
                #     serializer.save()
                # else:
                #     transaction.set_rollback(True)  # -----Rollback Transaction----
                #     copy_errors = serializer.errors.copy()
                #     # copy_errors.update(user_profile_serializer.errors)
                #     return Response(response.parsejson(copy_errors, "", status=403))

                # ---------------Profile address------------
                profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                        "state": state, "postal_code": postal_code, "status": 1, "added_by": user_id,
                                        "updated_by": user_id}
                serializer = ProfileAddressSerializer(data=profile_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                profile_home_address_data = {"user": user_id, "address_type": 1, "address_first": address_first,
                                             "state": state, "postal_code": postal_code, "status": 1,
                                             "added_by": user_id,
                                             "updated_by": user_id}
                serializer = ProfileAddressSerializer(data=profile_home_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # -------------User network------------
                user_network = {"domain": site_id, "user": user_id, "is_agent": 1, "status": status,
                                "agent_added_on": timezone.now()}
                serializer = NetworkUserSerializer(data=user_network)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    # -----------------Permission----------------
                    UserPermission.objects.filter(user=user_id, domain=site_id).delete()
                    for permission_data in permission:
                        user_permission = UserPermission()
                        user_permission.domain_id = site_id
                        user_permission.user_id = user_id
                        user_permission.permission_id = permission_data['permission_id']
                        user_permission.is_permission = permission_data['is_permission']
                        user_permission.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            # ------------------------Email-----------------------
            #extra_data = {"user_name": first_name, "email": email, "password": phone_no}
            template_data = {"domain_id": site_id, "slug": "agent_added"}
            #activation_link = settings.RESET_PASSWORD_URL + "/activation/?token=" + str(activation_code)
            #user_image_link = None
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            user_image_link = None
            broker_detail = Users.objects.get(site_id=site_id)
            broker_name = broker_detail.first_name
            broker_email = broker_detail.email
            if "profile_image" in data and data['profile_image'] != "":
                user_details = Users.objects.get(id=user_id)
                upload = UserUploads.objects.get(id=int(user_details.profile_image))
                bucket_name = upload.bucket_name
                image = upload.doc_file_name
                # user_image_link = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
                user_image_link = settings.AWS_URL + bucket_name+'/'+image
            domain_url = subdomain_url.replace("###", domain_name)+"edit-profile"
            domain_name_url = subdomain_url.replace("###", domain_name)
            extra_data = {"user_name": first_name, "user_image_link": user_image_link, "web_url": settings.FRONT_BASE_URL, "user_address": address_first, "user_company": "Dummy", "user_license_no": "012333", "user_phone": phone_format(phone_no), "user_email": email, "dashboard_link": domain_url, "domain_id": site_id, 'domain_name': domain_name_url, 'password': phone_no, 'name': first_name}
            compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
            #=============send broker==============
            template_data = {"domain_id": site_id, "slug": "agent_added_broker"}
            domain_url = subdomain_url.replace("###", domain_name)+"admin/agents/"
            extra_data = {"user_name": broker_name, "user_image_link": user_image_link, "web_url": settings.FRONT_BASE_URL, "user_address": address_first, "user_company": "Dummy", "user_license_no": "012333", "user_phone": phone_format(phone_no), "user_email": email, "dashboard_link": domain_url, "domain_id": site_id, 'domain_name': domain_name_url, 'password': phone_no, 'name': first_name}
            compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            
            # add notif to agent
            try:
                add_notification(
                    site_id,
                    title="Create Agent",
                    content="Welcome! You are now sub admin!",
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=2,
                    notification_type=3
                )
            except Exception as e:
                print(e)
                pass
            return Response(response.parsejson("Sub Admin Created Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))            


class SubdomainUpdateAgentApiView(APIView):
    """
    Subdomain update agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, network_user__is_agent=1, network_user__domain=site_id, user_type=2).first()
                if users is None:
                    # Translators: This message appears when user not exist
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                business = UserBusinessProfile.objects.filter(email__iexact=email).exclude(user=user_id).first()
                if business:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                # business = UserBusinessProfile.objects.filter(phone_no=phone_no).exclude(user=user_id).first()
                # if business:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            mobile_no = None
            if "mobile_no" in data and data['mobile_no'] != "":
                mobile_no = int(data['mobile_no'])
                users = Users.objects.filter(Q(user_business_profile__mobile_no=mobile_no)).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))

            if "company_name" in data and data['company_name'] != "":
                company_name = data['company_name']
            else:
                return Response(response.parsejson("company_name is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "address_first" in data and data['address_first'] != "":
                address_first = data['address_first']
            else:
                return Response(response.parsejson("address_first is required", "", status=403))

            if "state" in data and data['state'] != "":
                state = data['state']
            else:
                return Response(response.parsejson("state is required", "", status=403))

            if "postal_code" in data and data['postal_code'] != "":
                postal_code = data['postal_code']
            else:
                return Response(response.parsejson("postal_code is required", "", status=403))

            if "licence_no" in data and data['licence_no'] != "":
                licence_no = data['licence_no']
            else:
                licence_no = None

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required", "", status=403))

            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            company_logo = None
            if "company_logo" in data and data['company_logo'] != "":
                company_logo = int(data['company_logo'])

            if "permission" in data and len(data['permission']) > 0:
                permission = data['permission']
            else:
                return Response(response.parsejson("permission is required", "", status=403))

            with transaction.atomic():
                # -------------User-------------
                try:
                    Users.objects.filter(id=user_id).update(profile_image=profile_image)
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

                # -------------Business profile-----------
                # business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                #                  "first_name": first_name, "last_name": last_name, "address_first": address_first,
                #                  "state": state, "postal_code": postal_code, "licence_no": licence_no, "status": 1,
                #                  "company_logo": company_logo}
                business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                                 "first_name": first_name, "last_name": last_name, "licence_no": licence_no, "status": 1,
                                 "company_logo": company_logo}

                business = UserBusinessProfile.objects.filter(user=user_id, status=1).first()
                serializer = UserBusinessProfileSerializer(business, data=business_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # ---------------Profile address------------
                profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                        "state": state, "postal_code": postal_code, "status": 1,
                                        "added_by": user_id, "updated_by": user_id}
                ProfileAddress.objects.filter(user=user_id, address_type=2).delete()
                serializer = ProfileAddressSerializer(data=profile_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # -------------User network------------
                try:
                    NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1).update(status=status)
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

                try:
                    # -----------------Permission----------------
                    UserPermission.objects.filter(user=user_id, domain=site_id).delete()
                    for permission_data in permission:
                        user_permission = UserPermission()
                        user_permission.domain_id = site_id
                        user_permission.user_id = user_id
                        user_permission.permission_id = permission_data['permission_id']
                        user_permission.is_permission = permission_data['is_permission']
                        user_permission.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Agent updated successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubAdminUpdateApiView(APIView):
    """
    Sub Admin Update
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, network_user__is_agent=1, network_user__domain=site_id, user_type=4).first()
                if users is None:
                    # Translators: This message appears when user not exist
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                business = UserBusinessProfile.objects.filter(email__iexact=email).exclude(user=user_id).first()
                if business:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = int(data['phone_no'])
                # business = UserBusinessProfile.objects.filter(phone_no=phone_no).exclude(user=user_id).first()
                # if business:
                #     # Translators: This message appears when phone no already in db
                #     return Response(response.parsejson("Phone no already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            mobile_no = None
            if "mobile_no" in data and data['mobile_no'] != "":
                mobile_no = int(data['mobile_no'])
                users = Users.objects.filter(Q(user_business_profile__mobile_no=mobile_no)).exclude(id=user_id).first()
                if users:
                    # Translators: This message appears when phone no already in db
                    return Response(response.parsejson("Mobile no already exist", "", status=403))

            # if "company_name" in data and data['company_name'] != "":
            #     company_name = data['company_name']
            # else:
            #     return Response(response.parsejson("company_name is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "address_first" in data and data['address_first'] != "":
                address_first = data['address_first']
            else:
                return Response(response.parsejson("address_first is required", "", status=403))

            if "state" in data and data['state'] != "":
                state = data['state']
            else:
                return Response(response.parsejson("state is required", "", status=403))

            if "postal_code" in data and data['postal_code'] != "":
                postal_code = data['postal_code']
            else:
                return Response(response.parsejson("postal_code is required", "", status=403))

            # if "licence_no" in data and data['licence_no'] != "":
            #     licence_no = data['licence_no']
            # else:
            #     licence_no = None

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                return Response(response.parsejson("status is required", "", status=403))

            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            # company_logo = None
            # if "company_logo" in data and data['company_logo'] != "":
            #     company_logo = int(data['company_logo'])

            if "permission" in data and len(data['permission']) > 0:
                permission = data['permission']
            else:
                return Response(response.parsejson("permission is required", "", status=403))

            with transaction.atomic():
                # -------------User-------------
                try:
                    Users.objects.filter(id=user_id).update(profile_image=profile_image)
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

                users = Users.objects.filter(id=user_id).first()
                serializer = UsersSerializer(users, data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))    

                # -------------Business profile-----------
                # business_data = {"user": user_id, "company_name": company_name, "email": email, "phone_no": phone_no,
                #                  "first_name": first_name, "last_name": last_name, "licence_no": licence_no, "status": 1,
                #                  "company_logo": company_logo}

                # business = UserBusinessProfile.objects.filter(user=user_id, status=1).first()
                # serializer = UserBusinessProfileSerializer(business, data=business_data)
                # if serializer.is_valid():
                #     serializer.save()
                # else:
                #     transaction.set_rollback(True)  # -----Rollback Transaction----
                #     copy_errors = serializer.errors.copy()
                #     # copy_errors.update(user_profile_serializer.errors)
                #     return Response(response.parsejson(copy_errors, "", status=403))

                # ---------------Profile address------------
                profile_address_data = {"user": user_id, "address_type": 2, "address_first": address_first,
                                        "state": state, "postal_code": postal_code, "status": 1,
                                        "added_by": user_id, "updated_by": user_id}
                ProfileAddress.objects.filter(user=user_id, address_type=2).delete()
                serializer = ProfileAddressSerializer(data=profile_address_data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    # copy_errors.update(user_profile_serializer.errors)
                    return Response(response.parsejson(copy_errors, "", status=403))

                # -------------User network------------
                try:
                    NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1).update(status=status)
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

                try:
                    # -----------------Permission----------------
                    UserPermission.objects.filter(user=user_id, domain=site_id).delete()
                    for permission_data in permission:
                        user_permission = UserPermission()
                        user_permission.domain_id = site_id
                        user_permission.user_id = user_id
                        user_permission.permission_id = permission_data['permission_id']
                        user_permission.is_permission = permission_data['is_permission']
                        user_permission.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Sub Admin Updated Successfully", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))            


class SubdomainAgentDetailApiView(APIView):
    """
    Subdomain Agent detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, network_user__is_agent=1, network_user__domain=site_id, user_type=2).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            users = Users.objects.get(id=user_id, network_user__is_agent=1, network_user__domain=site_id)
            serializer = SubdomainAgentDetailSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch Data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubAdminDetailApiView(APIView):
    """
    Sub Admin Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, network_user__is_agent=1, network_user__domain=site_id, user_type=4).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            users = Users.objects.get(id=user_id, network_user__is_agent=1, network_user__domain=site_id)
            serializer = SubAdminDetailSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch Data", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))            


class SubdomainAgentListingApiView(APIView):
    """
    Subdomain Agent Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                except_user = None
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != site_id:
                    except_user = user_id
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            users = Users.objects.filter(network_user__domain=site_id, user_type=2, network_user__is_agent=1).exclude(id=except_user)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = str(data['search'])
                if search.isdigit():
                    users = users.filter(Q(id=search) | Q(user_business_profile__phone_no=search) | Q(user_business_profile__postal_code__icontains=search))
                else:
                    users = users.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(user_business_profile__email__icontains=search) | Q(user_business_profile__first_name__icontains=search) | Q(user_business_profile__last_name__icontains=search) | Q(user_business_profile__company_name__icontains=search) | Q(user_business_profile__licence_no__icontains=search) | Q(user_business_profile__address_first__icontains=search) | Q(user_business_profile__state__iso_name__icontains=search) | Q(full_name__icontains=search))
            # ---------------Filter--------------
            if "status" in data and len(data['status']) > 0:
                status = data['status']
                users = users.filter(status__in=status)

            total = users.count()
            users = users.order_by("-network_user__id").only('id')[offset:limit]
            serializer = SubdomainAgentListingSerializer(users, many=True, context=site_id)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
        

class SubAdminListingApiView(APIView):
    """
    Sub Admin Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                except_user = None
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, user_type__in=[2, 4], status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != site_id:
                    except_user = user_id
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            users = Users.objects.filter(network_user__domain=site_id, user_type=4, network_user__is_agent=1).exclude(id=except_user)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = str(data['search'])
                if search.isdigit():
                    users = users.filter(Q(id=search) | Q(phone_no=search) | Q(profile_address_user__postal_code__icontains=search))
                else:
                    users = users.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(profile_address_user__address_first__icontains=search) | Q(profile_address_user__state__iso_name__icontains=search) | Q(full_name__icontains=search))
            users = users.distinct()
            # ---------------Filter--------------
            if "status" in data and len(data['status']) > 0:
                status = data['status']
                users = users.filter(status__in=status)

            total = users.count()
            users = users.order_by("-id").only('id')[offset:limit]
            serializer = SubAdminListingSerializer(users, many=True, context=site_id)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))        


class SubdomainDeleteAgentApiView(APIView):
    """
    Subdomain delete agent
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            NetworkUser.objects.filter(domain=site_id, user=user_id).update(is_agent=0, is_upgrade=0)
            #Email send
            user_data = Users.objects.get(id=user_id)
            template_data = {"domain_id": site_id, "slug": "upgrade_user"}
            user_name = user_data.first_name if user_data.first_name is not None else ""
            user_email = user_data.email if user_data.email is not None else ""
            subdomain_url = settings.SUBDOMAIN_URL
            domain_name = network.domain_name
            dashboard_link = subdomain_url.replace("###", domain_name)+"edit-profile"
            if "deleted_by" in data and data['deleted_by'] != "":
                deleted_by = int(data['deleted_by'])
                delete_data = Users.objects.get(id=deleted_by)
                upg_user_name = delete_data.first_name
                upg_user_email = delete_data.email
                upg_user_phone = delete_data.phone_no
                domain_name = network.domain_name
                if int(delete_data.user_type.id) == 2 and delete_data.site_id is None:
                    user_type = 'Agent'
                else:
                    user_type = 'Broker'
                if user_email != "":
                    extra_data = {
                        "domain_id": site_id,
                        "user_name": user_name,
                        "dashboard_link": dashboard_link,
                        "user_type": user_type,
                        "name": upg_user_name,
                        "email": upg_user_email,
                        "phone": phone_format(upg_user_phone),
                        "domain_name": domain_name.title()
                        }
                    compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            # add notif to agent
            try:
                add_notification(
                    site_id,
                    title="Downgrade Agent",
                    content="You have been downgraded to user from " + domain_name + " agent!",
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=1,
                    notification_type=5
                )
            except Exception as e:
                print(e)
                pass
            return Response(response.parsejson("Agent deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainDeleteUserApiView(APIView):
    """
    Subdomain delete user
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            NetworkUser.objects.filter(domain=site_id, user=user_id).delete()
            return Response(response.parsejson("User deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserResetPasswordApiView(APIView):
    """
    Subdomain user reset password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is None:
                    return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))

            user.encrypted_password = b64encode(password)
            user.password = make_password(password)
            user.save()
            # Send Email ==============
            if "admin_id" in data and data['admin_id']:
                admin_id = int(data['admin_id'])
                user_data = Users.objects.get(id=user_id)
                user_name = user_data.first_name if user_data.first_name is not None else ""
                user_email = user_data.email if user_data.email is not None else ""
                admin_data = Users.objects.get(id=admin_id)
                admin_name = admin_data.first_name if admin_data.first_name is not None else ""
                admin_email = admin_data.email if admin_data.email is not None else ""
                template_data = {"domain_id": site_id, "slug": "user_reset_password"}
                domain_name = network.domain_name
                extra_data = {
                    "domain_id": site_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "name": admin_name,
                    "email": admin_email,
                    "password": password,
                    "domain_name": domain_name.title()
                }
                compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Reset password successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserChangePasswordApiView(APIView):
    """
    Subdomain user change password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))

                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is None:
                    return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))

            if "new_password" in data and data['new_password'] != "":
                new_password = data['new_password']
            else:
                return Response(response.parsejson("new_password is required", "", status=403))

            if password == new_password:
                return Response(response.parsejson("New password should be different from old password. ", "", status=403))

            if not check_password(password, user.password):
                return Response(response.parsejson("Old password not matched.", "", status=403))

            user.encrypted_password = b64encode(new_password)
            user.password = make_password(new_password)
            user.save()
            # Send Email ==============
            if "admin_id" in data and data['admin_id']:
                admin_id = int(data['admin_id'])
                user_data = Users.objects.get(id=user_id)
                user_name = user_data.first_name if user_data.first_name is not None else ""
                user_email = user_data.email if user_data.email is not None else ""
                admin_data = Users.objects.get(id=admin_id)
                admin_name = admin_data.first_name if admin_data.first_name is not None else ""
                admin_email = admin_data.email if admin_data.email is not None else ""
                template_data = {"domain_id": site_id, "slug": "subdomain_changed_password"}
                domain_name = network.domain_name
                extra_data = {
                    "domain_id": site_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "name": admin_name,
                    "email": admin_email,
                    "password": new_password,
                    "domain_name": domain_name.title()
                }
                compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Password changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserChangePasswordApiView(APIView):
    """
    User change password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))

            if "new_password" in data and data['new_password'] != "":
                new_password = data['new_password']
            else:
                return Response(response.parsejson("new_password is required", "", status=403))

            if password == new_password:
                return Response(response.parsejson("New password should be different from old password.", "", status=403))

            if not check_password(password, user.password):
                return Response(response.parsejson("Old password not matched.", "", status=403))

            user.encrypted_password = b64encode(new_password)
            user.password = make_password(new_password)
            user.save()
            return Response(response.parsejson("Password changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainWebsiteDetailApiView(APIView):
    """
    Subdomain website detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=2).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != site_id:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1, user__user_type=2).first()
                    if network_user is None:
                        return Response(response.parsejson("You can't access.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            network_domain = NetworkDomain.objects.get(id=site_id, is_active=1)
            serializer = SubdomainWebsiteDetailSerializer(network_domain)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainWebsiteUpdateApiView(APIView):
    """
    Subdomain website update
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=2).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != site_id:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1, user__user_type=2).first()
                    if network_user is None:
                        return Response(response.parsejson("You can't update website values.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "domain_url" in data and data['domain_url'] != "":
                domain_url = data['domain_url']
                network_domain = NetworkDomain.objects.filter(domain_url=domain_url).exclude(id=site_id).first()
                if network_domain is not None:
                    return Response(response.parsejson("Domain url already exist", "", status=403))
            else:
                return Response(response.parsejson("domain_url is required", "", status=403))

            if "bot_setting" in data and type(data['bot_setting']) == list and len(data['bot_setting']) > 0:
                bot_setting = data['bot_setting']
            else:
                return Response(response.parsejson("bot_setting is required", "", status=403))

            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name']
                network_domain = NetworkDomain.objects.filter(domain_name=domain_name).exclude(id=site_id).first()
                if network_domain is not None:
                    return Response(response.parsejson("Domain name already exist", "", status=403))
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            banner_images = None
            if "banner_images" in data and len(data['banner_images']) > 0:
                banner_images = data['banner_images']

            footer_images = None
            if "footer_images" in data and len(data['footer_images']) > 0:
                footer_images = data['footer_images']

            if "auctions" in data and len(data['auctions']) > 0:
                auctions = data['auctions']
            else:
                return Response(response.parsejson("auctions is required", "", status=403))

            if "expertise" in data and len(data['expertise']) > 0:
                expertise = data['expertise']
            else:
                return Response(response.parsejson("expertise is required", "", status=403))

            if "social_account" in data and len(data['social_account']) > 0:
                social_account = data['social_account']
            else:
                return Response(response.parsejson("social_account is required", "", status=403))

            if "dashboard_numbers" in data and len(data['dashboard_numbers']) > 0:
                dashboard_numbers = data['dashboard_numbers']
            else:
                return Response(response.parsejson("dashboard_numbers is required", "", status=403))

            mls_type = None
            api_key = None
            originating_system = None
            if "mls_type" in data and data['mls_type'] != "":
                mls_type = int(data['mls_type'])
                if mls_type == 3:
                    if "originating_system" in data and data['originating_system'] != "":
                        originating_system = data['originating_system']
                    else:
                        return Response(response.parsejson("originating_system is required", "", status=403))

                if "api_key" in data and data['api_key'] != "":
                    api_key = data['api_key']
                else:
                    return Response(response.parsejson("api_key is required", "", status=403))

            # if "about_images" in data and len(data['about_images']) > 0:
            #     about_images = data['about_images']
            # else:
            #     return Response(response.parsejson("about_images is required", "", status=403))
            # -----------------Check subdomain url---------------
            subdomain_url = settings.SUBDOMAIN_URL
            raw_domain_url = subdomain_url.replace("###", domain_name)
            network_domain_detail = NetworkDomain.objects.filter(id=site_id).first()
            if raw_domain_url != domain_url and int(network_domain_detail.domain_type) != 1:
                return Response(response.parsejson("Subdomain name and url not matched.", "", status=403))

            data_field = ["favicon", "website_title", "website_logo", "banner_headline", "website_name",
                          "call_to_action", "extended_description", "about_title", "about_description"]
            raw_data = []
            for field in data_field:
                if field in data and data[field] != "":
                    tmp_data = {"domain_id": site_id, "settings_name": field, "setting_value": data[field],
                                "added_by": user_id, "updated_by": user_id}
                    raw_data.append(tmp_data)
                else:
                    return Response(response.parsejson(field+" is required", "", status=403))
            with transaction.atomic():
                # ----------------------Delete all existing data-----------------
                CustomSiteSettings.objects.filter(domain_id=site_id).delete()
                for row_data in raw_data:
                    serializer = CustomSiteSettingsSerializer(data=row_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------Update network domain-----------
                network_domain = NetworkDomain.objects.filter(id=site_id).first()
                network_domain.domain_name = domain_name
                network_domain.domain_url = domain_url
                network_domain.save()

                # -----------Delete all existing data---------
                NetworkUpload.objects.filter(domain=site_id, upload_type=1).delete()
                # --------------Banner entry--------------
                if banner_images is not None:
                    for images in banner_images:
                        temp = {"domain": site_id, "upload": images, "upload_type": 1, 'status': 1,
                                "added_by": user_id, "updated_by": user_id}
                        serializer = NetworkUploadSerializer(data=temp)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                # -----------Delete all existing data---------
                NetworkUpload.objects.filter(domain=site_id, upload_type=2).delete()
                # ------------------Footer images insert----------------
                if footer_images is not None:
                    for images in footer_images:
                        temp = {"domain": site_id, "upload": images, "upload_type": 2, 'status': 1,
                                "added_by": user_id, "updated_by": user_id}
                        serializer = NetworkUploadSerializer(data=temp)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete auction--------------
                NetworkAuction.objects.filter(domain=site_id).delete()
                for auction in auctions:
                    auction['domain'] = site_id
                    auction['added_by'] = user_id
                    auction['updated_by'] = user_id
                    serializer = NetworkAuctionSerializer(data=auction)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete expertise--------------
                NetworkExpertise.objects.filter(domain=site_id).delete()
                for expert in expertise:
                    expert['domain'] = site_id
                    expert['added_by'] = user_id
                    expert['updated_by'] = user_id
                    serializer = NetworkExpertiseSerializer(data=expert)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete social account--------------
                NetworkSocialAccount.objects.filter(domain=site_id).delete()
                for account in social_account:
                    account['domain'] = site_id
                    account['added_by'] = user_id
                    account['updated_by'] = user_id
                    account['status'] = 1
                    serializer = NetworkSocialAccountSerializer(data=account)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete dashboard numbers--------------
                DashboardNumbers.objects.filter(domain=site_id).delete()
                for number in dashboard_numbers:
                    number['domain'] = site_id
                    number['added_by'] = user_id
                    number['updated_by'] = user_id
                    number['status'] = 1
                    serializer = DashboardNumbersSerializer(data=number)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
                # ----------------------Property bot-------------------------
                try:
                    PropertyEvaluatorSetting.objects.filter(domain=site_id).delete()
                    for property_type_id in bot_setting:
                        property_evaluator_setting = PropertyEvaluatorSetting()
                        property_evaluator_setting.domain_id = site_id
                        property_evaluator_setting.property_type_id = int(property_type_id)
                        property_evaluator_setting.status_id = 1
                        property_evaluator_setting.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

                # ----------------------MLS Configuration-------------------------
                try:
                    NetworkMlsConfiguration.objects.filter(domain=site_id).delete()
                    if mls_type is not None and api_key and not None:
                        network_mls_configuration = NetworkMlsConfiguration()
                        network_mls_configuration.api_key = api_key
                        network_mls_configuration.domain_id = site_id
                        network_mls_configuration.mls_type_id = mls_type
                        network_mls_configuration.status_id = 1
                        network_mls_configuration.originating_system = originating_system
                        network_mls_configuration.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("Website updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserDataCheckApiView(APIView):
    """
    User data check
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            site_id = None
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            user = Users.objects.exclude(id=user_id)
            if "email" in data and data['email'] != "":
                user_email = user.filter(email__iexact=data['email']).first()
                if user_email is not None:
                    return Response(response.parsejson("email already exist.", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                user_phone = user.filter(phone_no=data['phone_no']).first()
                if user_phone is not None:
                    return Response(response.parsejson("Phone no already exist.", "", status=403))
            network_domain = NetworkDomain.objects.exclude(id=site_id)
            if "domain_name" in data and data['domain_name'] != "":
                network_domain_name = network_domain.filter(domain_name=data['domain_name']).first()
                if network_domain_name is not None:
                    return Response(response.parsejson("Domain name already exist.", "", status=403))

            if "domain_url" in data and data['domain_url'] != "":
                network_domain_url = network_domain.filter(domain_url=data['domain_url']).first()
                if network_domain_url is not None:
                    return Response(response.parsejson("Domain url already exist.", "", status=403))

            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NetworkDomainlistApiView(APIView):
    """
    Network Domain List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            network_domain = NetworkDomain.objects.filter(id__gte=1, is_delete=False).order_by("-id").values('id', 'domain_name', 'is_active', 'domain_type', 'domain_url')
            return Response(response.parsejson("Fetch Data.", network_domain, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserResetPasswordApiView(APIView):
    """
    Admin user reset password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))
            
            if user.encrypted_password == b64encode(password):
                return Response(response.parsejson("New password should be different from old password. ", "", status=403))

            user.encrypted_password = b64encode(password)
            user.password = make_password(password)
            user.save()
            #send Email =================
            user_data = Users.objects.get(id=user_id)
            user_email = user_data.email if user_data.email is not None else ""
            user_name = user_data.first_name if user_data.first_name is not None else ""
            super_data = Users.objects.get(user_type=3)
            admin_name = super_data.first_name if super_data.first_name is not None else ""
            admin_email = super_data.email if super_data.email is not None else ""
            template_data = {"domain_id": "", "slug": "super_admin_change_password"}
            extra_data = {
                "user_name": user_name,
                "user_email": user_email,
                "password": password,
                "name": admin_name,
                "email": admin_email
            }
            compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Reset password successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserChangePasswordApiView(APIView):
    """
    Admin user change password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))

            if "new_password" in data and data['new_password'] != "":
                new_password = data['new_password']
            else:
                return Response(response.parsejson("new_password is required", "", status=403))

            if password == new_password:
                return Response(response.parsejson("New password should be different from old password. ", "", status=403))

            if not check_password(password, user.password):
                return Response(response.parsejson("Old password not matched.", "", status=403))

            user.encrypted_password = b64encode(new_password)
            user.password = make_password(new_password)
            user.save()
            return Response(response.parsejson("Password changed successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminProfileDetailApiView(APIView):
    """
    Admin profile detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=3).first()
                if users is None:
                    return Response(response.parsejson("User Not Exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            users = Users.objects.filter(id=user_id, status=1).values('id', "first_name", "last_name", "phone_no", "email")
            return Response(response.parsejson("Fetch Data", users, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminProfileUpdateApiView(APIView):
    """
    Admin profile update
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=3).first()
                if users is None:
                    return Response(response.parsejson("User Not Exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = data['phone_no']
                users = Users.objects.filter(phone_no=phone_no).exclude(id=user_id).first()
                if users is not None:
                    return Response(response.parsejson("Phone no already exist.", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                users = Users.objects.filter(email__iexact=email).exclude(id=user_id).first()
                if users is not None:
                    return Response(response.parsejson("Email already exist.", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            Users.objects.filter(id=user_id).update(first_name=first_name, last_name=last_name, phone_no=phone_no, email=email)
            return Response(response.parsejson("Profile updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSubdomainListingApiView(APIView):
    """
    AdminSubdomainListingApiView
    """

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page
            network_domain = NetworkDomain.objects.filter(id__gte=1, is_delete=False)
            # -----------------Search-------------------
            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                if 1 in data['status'] or '1' in data['status'] and len(data['status']) == 1:
                    network_domain = network_domain.filter(is_active=True)
                if 0 in data['status'] or '0' in data['status'] and len(data['status']) == 1:
                    network_domain = network_domain.filter(is_active=False)

            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_domain = network_domain.filter(Q(id=search))
                else:
                    network_domain = network_domain.annotate(
                        full_name=Concat('users_site_id__first_name', V(' '), 'users_site_id__last_name')).filter(
                        Q(domain_name__icontains=search) | Q(domain_url__icontains=search) | Q(
                            users_site_id__first_name__icontains=search) | Q(
                            users_site_id__last_name__icontains=search) | Q(users_site_id__email__icontains=search) | Q(
                            full_name__icontains=search))
            total = network_domain.count()
            network_domain = network_domain.order_by("-id").only('id')[offset: limit]
            serializer = AdminSubdomainListingSerializer(network_domain, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSubdomainDetailApiView(APIView):
    """
    Admin subdomain detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            network_domain = NetworkDomain.objects.get(id=site_id)
            serializer = AdminSubdomainDetailSerializer(network_domain)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSubdomainUpdateApiView(APIView):
    """
    Admin subdomain detail save
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "domain_url" in data and data['domain_url'] != "":
                domain_url = data['domain_url']
                network_domain = NetworkDomain.objects.filter(domain_url=domain_url).exclude(id=site_id).first()
                if network_domain is not None:
                    return Response(response.parsejson("Domain url already exist", "", status=403))
            else:
                return Response(response.parsejson("domain_url is required", "", status=403))

            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name']
                network_domain = NetworkDomain.objects.filter(domain_name=domain_name).exclude(id=site_id).first()
                if network_domain is not None:
                    return Response(response.parsejson("Domain name already exist", "", status=403))
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            # if "articles" in data and len(data['articles']) > 0:
            #     articles = data['articles']
            # else:
            #     return Response(response.parsejson("articles is required", "", status=403))

            banner_images = None
            if "banner_images" in data and len(data['banner_images']) > 0:
                banner_images = data['banner_images']

            footer_images = None
            if "footer_images" in data and len(data['footer_images']) > 0:
                footer_images = data['footer_images']

            if "auctions" in data and len(data['auctions']) > 0:
                auctions = data['auctions']
            else:
                return Response(response.parsejson("auctions is required", "", status=403))

            if "expertise" in data and len(data['expertise']) > 0:
                expertise = data['expertise']
            else:
                return Response(response.parsejson("expertise is required", "", status=403))

            if "social_account" in data and len(data['social_account']) > 0:
                social_account = data['social_account']
            else:
                return Response(response.parsejson("social_account is required", "", status=403))

            if "dashboard_numbers" in data and len(data['dashboard_numbers']) > 0:
                dashboard_numbers = data['dashboard_numbers']
            else:
                return Response(response.parsejson("dashboard_numbers is required", "", status=403))

            # if "about_images" in data and len(data['about_images']) > 0:
            #     about_images = data['about_images']
            # else:
            #     return Response(response.parsejson("about_images is required", "", status=403))
            # -----------------Check subdomain url---------------
            subdomain_url = settings.SUBDOMAIN_URL
            raw_domain_url = subdomain_url.replace("###", domain_name)
            if raw_domain_url != domain_url:
                return Response(response.parsejson("Subdomain name and url not matched.", "", status=403))

            data_field = ["favicon", "website_title", "website_logo", "banner_headline", "website_name",
                          "call_to_action", "extended_description", "about_title", "about_description"]
            raw_data = []
            for field in data_field:
                if field in data and data[field] != "":
                    tmp_data = {"domain_id": site_id, "settings_name": field, "setting_value": data[field],
                                "added_by": user_id, "updated_by": user_id}
                    raw_data.append(tmp_data)
                else:
                    return Response(response.parsejson(field+" is required", "", status=403))
            with transaction.atomic():
                # ----------------------Delete all existing data-----------------
                CustomSiteSettings.objects.filter(domain_id=site_id).delete()
                for row_data in raw_data:
                    serializer = CustomSiteSettingsSerializer(data=row_data)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------Update network domain-----------
                network_domain = NetworkDomain.objects.filter(id=site_id).first()
                network_domain.domain_name = domain_name
                network_domain.domain_url = domain_url
                network_domain.save()

                # -----------Delete all existing data---------
                NetworkUpload.objects.filter(domain=site_id, upload_type=1).delete()
                # --------------Banner entry--------------
                if banner_images is not None:
                    for images in banner_images:
                        temp = {"domain": site_id, "upload": images, "upload_type": 1, 'status': 1,
                                "added_by": user_id, "updated_by": user_id}
                        serializer = NetworkUploadSerializer(data=temp)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                # -----------Delete all existing data---------
                NetworkUpload.objects.filter(domain=site_id, upload_type=2).delete()
                # ------------------Footer images insert----------------
                if footer_images is not None:
                    for images in footer_images:
                        temp = {"domain": site_id, "upload": images, "upload_type": 2, 'status': 1,
                                "added_by": user_id, "updated_by": user_id}
                        serializer = NetworkUploadSerializer(data=temp)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete auction--------------
                NetworkAuction.objects.filter(domain=site_id).delete()
                for auction in auctions:
                    auction['domain'] = site_id
                    auction['added_by'] = user_id
                    auction['updated_by'] = user_id
                    serializer = NetworkAuctionSerializer(data=auction)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete expertise--------------
                NetworkExpertise.objects.filter(domain=site_id).delete()
                for expert in expertise:
                    expert['domain'] = site_id
                    expert['added_by'] = user_id
                    expert['updated_by'] = user_id
                    serializer = NetworkExpertiseSerializer(data=expert)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete social account--------------
                NetworkSocialAccount.objects.filter(domain=site_id).delete()
                for account in social_account:
                    account['domain'] = site_id
                    account['added_by'] = user_id
                    account['updated_by'] = user_id
                    account['status'] = 1
                    serializer = NetworkSocialAccountSerializer(data=account)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                # ------------------Delete dashboard numbers--------------
                DashboardNumbers.objects.filter(domain=site_id).delete()
                for number in dashboard_numbers:
                    number['domain'] = site_id
                    number['added_by'] = user_id
                    number['updated_by'] = user_id
                    number['status'] = 1
                    serializer = DashboardNumbersSerializer(data=number)
                    if serializer.is_valid():
                        serializer.save()
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Website updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSubdomainChangeStatusApiView(APIView):
    """
    Admin subdomain change status
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "is_active" in data and data['is_active'] != "":
                is_active = int(data['is_active'])
                if int(is_active) == 1:
                    template_data = {"domain_id": "", "slug": "domain_activated"}
                else:
                    template_data = {"domain_id": "", "slug": "domain_de-activated"}
            else:
                return Response(response.parsejson("is_active is required", "", status=403))

            NetworkDomain.objects.filter(id=site_id).update(is_active=is_active)
            #send Email====================
            user_data = Users.objects.get(site_id=site_id)
            user_name = user_data.first_name if user_data.first_name is not None else ""
            user_email = user_data.email if user_data.email is not None else ""
            super_data = Users.objects.get(id=user_id)
            super_name = super_data.first_name if super_data.first_name is not None else ""
            super_email = super_data.email if super_data.email is not None else ""
            domain_name = network.domain_name
            subdomain_url = settings.SUBDOMAIN_URL
            domain_url = subdomain_url.replace("###", domain_name)
            extra_data = {
                "user_name": user_name,
                "domain_url": domain_url,
                "name": super_name,
                "email": super_email    
            }
            compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Status updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserDashBoardCountingsApiView(APIView):
    """ Api's to provide admin dashboard user, subscription
    and payments count details.
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            all_data = {}
            # perform user calculations
            users = Users.objects.filter(status=1).exclude(user_type=3)
            all_data['total_users'] = users.count()
            all_data['total_buyer_seller'] = users.filter(user_type=1).count()
            all_data['total_brokers'] = users.filter(user_type=2, site__isnull=False).count()
            all_data['total_agents'] = users.filter(user_type=2, site__isnull=True).count()
            # over last week changes in user registration
            date = datetime.date.today()
            end_week = date - datetime.timedelta(date.weekday())
            start_week = end_week - datetime.timedelta(7)
            # get previouw week users
            previous_week_user_count = users.filter(added_on__lt=start_week).count()
            previous_week_buyer_seller_count = users.filter(added_on__lt=start_week, user_type=1).count()
            previous_week_brokers_count = users.filter(added_on__lt=start_week,  user_type=2, site__isnull=False).count()
            previous_week_agents_count = users.filter(added_on__lt=start_week,  user_type=2, site__isnull=True).count()

            all_data['change_total_user'] = (all_data['total_users'] - previous_week_user_count)/previous_week_user_count*100 if previous_week_user_count else 100
            all_data['change_buyer_seller'] = (all_data['total_buyer_seller'] - previous_week_buyer_seller_count)/previous_week_buyer_seller_count*100 if previous_week_buyer_seller_count else 100
            all_data['change_brokers'] = (all_data['total_brokers'] - previous_week_brokers_count)/previous_week_brokers_count*100 if previous_week_brokers_count else 100
            all_data['change_agents'] = (all_data['total_agents'] - previous_week_agents_count)/previous_week_agents_count*100 if previous_week_agents_count else 100
            
            # paid users
            paid_users = UserSubscription.objects\
                .filter(payment_status=1, subscription_status=1, opted_plan__subscription_id__in=[3, 4], user__status=1)\
                .exclude(user__user_type=3)

            # get paid users
            all_data['total_paid_users'] = paid_users.count()
            # get previouw week paid users
            prev_week_paid_user_count = paid_users.filter(added_on__lt=start_week).count()
            # get current week paid users
            all_data['change_total_paid_user'] = (all_data['total_paid_users'] - prev_week_paid_user_count)/prev_week_paid_user_count*100 if prev_week_paid_user_count else 100

            # total revenue count
            paid_subscriptions = UserSubscription.objects\
                .filter(payment_status=1, opted_plan__subscription_id__in=[3, 4], user__status=1)\
                .exclude(user__user_type=3)
            # get total revenue
            all_data['total_revenue'] = paid_subscriptions.aggregate(Sum('payment_amount'))['payment_amount__sum']
            all_data['total_revenue'] =  all_data['total_revenue'] if all_data['total_revenue'] else 0
            
            # get previouw week revenue
            prev_week_revenue = paid_subscriptions\
                                        .filter(added_on__lt=start_week)\
                                        .aggregate(Sum('payment_amount'))['payment_amount__sum']
            prev_week_revenue = prev_week_revenue if prev_week_revenue else 0                          
            all_data['change_total_revenue'] = (all_data['total_revenue'] - prev_week_revenue)/prev_week_revenue*100 if prev_week_revenue else 100

            # last 7 days properties
            before_7_days = date - datetime.timedelta(days=7)
            properties = PropertyListing.objects\
                .filter(added_on__date__gt=before_7_days)\
                .extra(select={'day': 'date( added_on )'})\
                .values('day')\
                .annotate(
                    count=Count('id')
                )\
                .order_by('day')
            
            # append 0 if no lsiting created for a date
            items = list(properties)
            dates = [x.get('day') for x in items]
            for d in (date - datetime.timedelta(days=x) for x in range(0,8)):
                if d not in dates:
                    items.append({'day': d, 'count': 0})
            items.sort(key=lambda r: r['day'])
            all_data['last_seven_days_prop_count'] = {'day': [ x.get('day') for x in items ], 'counts': [ x.get('count') for x in items ]}
            all_data['prop_count'] = PropertyListing.objects.count()
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminUserDashBoardPropertyAnalyticsApiView(APIView):
    """ This is used to load daily property counting for
    analytics purpose

    Args:
        APIView (day): days in number to load how many days of data wants to be fetched

    Returns:
        [json]: [json object of day and count on each day]
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            days = 7
            if "days" in data and data['days'] != "":
                days = int(data['days'])

            all_data = {}
            date = datetime.date.today()
            # last 7 days properties
            last_day_date = date - datetime.timedelta(days=days)
            properties = PropertyListing.objects\
                .filter(added_on__date__gt=last_day_date)\
                .extra(select={'day': 'date( added_on )'})\
                .values('day')\
                .annotate(
                    count=Count('id')
                )\
                .order_by('day')
            
            # append 0 if no lsiting created for a date
            items = list(properties)
            dates = [x.get('day') for x in items]
            for d in (date - datetime.timedelta(days=x) for x in range(0,days + 1)):
                if d not in dates:
                    items.append({'day': d, 'count': 0})
            items.sort(key=lambda r: r['day'])
            all_data['last_seven_days_prop_count'] = {'day': [ x.get('day') for x in items ], 'counts': [ x.get('count') for x in items ]}
            all_data['prop_count'] = PropertyListing.objects.count()
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FileUploadApiView(APIView):
    """
    File upload
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            all_data = {}
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['site'] = site_id
            else:
                data['site'] = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                data['user'] = user_id

            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "doc_file_name" in data and data['doc_file_name'] != "":
                doc_file_name = data['doc_file_name']
            else:
                return Response(response.parsejson("doc_file_name is required", "", status=403))

            if "file_size" in data and data['file_size'] != "":
                file_size = data['file_size']
            else:
                data['file_size'] = None

            if "document_type" in data and data['document_type'] != "":
                document_type = int(data['document_type'])
                data['document'] = document_type
            else:
                data['document'] = None

            if "bucket_name" in data and data['bucket_name'] != "":
                bucket_name = data['bucket_name']
            else:
                return Response(response.parsejson("bucket_name is required", "", status=403))

            if "added_by" in data and data['added_by'] != "":
                added_by = int(data['added_by'])
                data['updated_by'] = added_by
            else:
                return Response(response.parsejson("added_by is required", "", status=403))

            data['is_active'] = 1
            serializer = UserUploadsSerializer(data=data)
            if serializer.is_valid():
                upload = serializer.save()
                all_data['upload_id'] = upload.id
                all_data['file_size'] = data['file_size']
                all_data['added_date'] = upload.added_on
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))

            return Response(response.parsejson("Upload successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeleteSettingFileApiView(APIView):
    """
    Delete setting file
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_admin = None
            if "is_admin" in data and data['is_admin'] != "":
                is_admin = data['is_admin']

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if is_admin is None:
                if "user_id" in data and data['user_id'] != "":
                    user_id = int(data['user_id'])
                    user = Users.objects.filter(id=user_id, status=1, user_type=2).first()
                    if user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    elif user.site_id != site_id:
                        network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1, user__user_type=2).first()
                        if network_user is None:
                            return Response(response.parsejson("User is not broker/agent.", "", status=403))
                else:
                    return Response(response.parsejson("user_id is required", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            if "upload_type" in data and data['upload_type'] != "":
                upload_type = data['upload_type'].lower()
                if upload_type == "banner_image":
                    upload_type_id = 1
                elif upload_type == "footer_company":
                    upload_type_id = 2
                elif upload_type == "about_mage":
                    upload_type_id = 3
                else:
                    upload_type_id = None
            else:
                return Response(response.parsejson("upload_type is required", "", status=403))
            with transaction.atomic():
                try:
                    if upload_type_id in [1, 2, 3]:
                        NetworkUpload.objects.filter(domain=site_id, upload=upload_id, upload_type=upload_type_id).delete()
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeleteArticleFileApiView(APIView):
    """
    Delete article file
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_admin = None
            if "is_admin" in data and data['is_admin'] != "":
                is_admin = data['is_admin']

            if is_admin is None:  # avoid checks on admin end
                if "site_id" in data and data['site_id'] != "":
                    site_id = int(data['site_id'])
                    network = NetworkDomain.objects.filter(id=site_id).first()
                    if network is None:
                        return Response(response.parsejson("Site not exist.", "", status=403))
                else:
                    return Response(response.parsejson("site_id is required", "", status=403))

                if "user_id" in data and data['user_id'] != "":
                    user_id = int(data['user_id'])
                    user = Users.objects.filter(id=user_id, status=1).first()
                    if user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    elif user.site_id != site_id:
                        network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1, status=1).first()
                        if network_user is None:
                            return Response(response.parsejson("User is not broker/agent.", "", status=403))
                else:
                    return Response(response.parsejson("user_id is required", "", status=403))

            article_id = None
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
            else:
                if is_admin is None:
                    return Response(response.parsejson("article_id is required", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            if "upload_type" in data and data['upload_type'] != "":
                upload_type = data['upload_type'].lower()
            else:
                return Response(response.parsejson("upload_type is required", "", status=403))

            with transaction.atomic():
                try:
                    if article_id is not None:
                        if upload_type == "article_image":
                            NetworkArticles.objects.filter(id=article_id).update(upload=None)
                        elif upload_type == "author_image":
                            NetworkArticles.objects.filter(id=article_id).update(author_image=None)
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TestEmailApiView(APIView):
    """
    Test email
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            extra_data = {"user_name": "Gautam Kumar"}

            # msg = "<h1> {welcome} </h1> <br/> Hi {user_name}, <br/> Welcome to Reba Website. <br/> Thanks, <br/> Team Bidhom"
            # mail_data = {"welcome": "Welcome bidhom", "user_name": "Gautam Kumar"}
            # content = msg.format(**mail_data)
            # html_content = render_to_string('email/email_header_footer.html', {"template_message_body": content, "web_url": settings.BASE_URL})

            # email = EmailMessage(subject, html_content, from_email, to=[email])
            # email.content_subtype = "html"
            # email.send()
            # send_mail(subject, msg, from_email, [email], html_message=html_content)
            # mail = EmailMultiAlternatives(subject, msg, from_email, [email])
            # mail.attach_alternative(html_content, "text/html")
            # mail.send()
            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeleteFileApiView(APIView):
    """
    Delete file
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                user_id = None

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            if "upload_type" in data and data['upload_type'] != "":
                upload_type = data['upload_type'].lower()
            else:
                return Response(response.parsejson("upload_type is required", "", status=403))

            with transaction.atomic():
                try:
                    if upload_type == "profile_image" and user_id is not None:
                        Users.objects.filter(id=user_id).update(profile_image=None)
                    elif upload_type == "auction_image":
                        NetworkAuction.objects.filter(upload=upload_id).update(upload=None)
                    elif upload_type == "expertise_image":
                        NetworkExpertise.objects.filter(upload=upload_id).update(upload=None)
                    elif upload_type == "company_logo":
                        UserBusinessProfile.objects.filter(user=user_id).update(company_logo=None)
                    elif upload_type == "advertisement":
                        Advertisement.objects.filter(image=upload_id).update(image=None)
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ArticleListingApiView(APIView):
    """
    Article listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            network_articles = NetworkArticles.objects.filter()
            if "status" in data and data["status"] != "":
                network_articles = network_articles.filter(status__in=data["status"])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_articles = network_articles.filter(Q(id=search))
                else:
                    network_articles = network_articles.filter(Q(title__icontains=search) | Q(author_name__icontains=search) | Q(asset__name__icontains=search))

            total = network_articles.count()
            network_articles = network_articles.order_by("-id").only("id")[offset:limit]
            serializer = ArticleListingSerializer(network_articles, many=True)
            all_data = {"total": total, "data": serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserDetailApiView(APIView):
    """
    Subdomain user detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))

                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is None:
                    return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            users = Users.objects.get(id=user_id)
            serializer = SubdomainUserDetailSerializer(users)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserUpdateApiView(APIView):
    """
    Subdomain user update
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))

                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                if network_user is None:
                    return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))

                users = Users.objects.filter(email__iexact=email).exclude(id=user_id).first()
                if users is not None:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = data['phone_no']
                users = Users.objects.filter(phone_no=phone_no).exclude(id=user_id).first()
                if users is not None:
                    # Translators: This message appears when phone number already in db
                    return Response(response.parsejson("Phone number already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))
            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            users = Users.objects.get(id=user_id)
            users.first_name = first_name
            users.last_name = last_name
            users.email = email
            users.phone_no = phone_no
            users.profile_image = profile_image
            users.save()
            return Response(response.parsejson("Data updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddArticleApiView(APIView):
    """
    Add/Update article
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                # data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            article_id = None
            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
                article_id = NetworkArticles.objects.get(id=article_id)

            required_field = ['title', "description", "author_name", "status", "user_id", "asset"]
            for field in required_field:
                if field in data and data[field] != "":
                    field = data[field]
                else:
                    return Response(response.parsejson(field+" is required", "", status=403))

            if "author_image" in data and data['author_image'] != "":
                author_image = int(data['author_image'])
            else:
                data['author_image'] = None

            if "upload" in data and data['upload'] != "":
                upload = int(data['upload'])
            else:
                data['upload'] = None
            if article_id is None:
                data['added_by'] = data['user_id']
            else:
                data['added_by'] = article_id.added_by_id
            data['updated_by'] = data['user_id']
            serializer = AddArticleSerializer(article_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Article successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ArticleDetailApiView(APIView):
    """
    Article detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "article_id" in data and data['article_id'] != "":
                article_id = int(data['article_id'])
            else:
                return Response(response.parsejson("article_id is required", "", status=403))

            network_articles = NetworkArticles.objects.get(id=article_id)
            serializer = ArticleDetailSerializer(network_articles)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserSuggestionApiView(APIView):
    """
    Subdomain user suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []
            users = Users.objects.annotate(data=Concat('first_name', V(' '), 'last_name')).filter(network_user__domain=site_id, network_user__is_agent=0, data__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('email')).filter(network_user__domain=site_id, network_user__is_agent=0, email__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('phone_no')).filter(network_user__domain=site_id, network_user__is_agent=0, phone_no__icontains=search).values("data")
            searched_data = searched_data + list(users)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainAgentSuggestionApiView(APIView):
    """
    Subdomain agent suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []
            users = Users.objects.annotate(data=Concat('user_business_profile__first_name', V(' '), 'user_business_profile__last_name')).filter(network_user__domain=site_id, network_user__is_agent=1, data__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('user_business_profile__email')).filter(network_user__domain=site_id, network_user__is_agent=1, user_business_profile__email__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('user_business_profile__phone_no')).filter(network_user__domain=site_id, network_user__is_agent=1, user_business_profile__phone_no__icontains=search).values("data")
            searched_data = searched_data + list(users)

            profile = UserBusinessProfile.objects.annotate(data=F('company_name')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, company_name__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            profile = UserBusinessProfile.objects.annotate(data=F('licence_no')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, licence_no__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            profile = UserBusinessProfile.objects.annotate(data=F('address_first')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, address_first__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            profile = UserBusinessProfile.objects.annotate(data=F('postal_code')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, postal_code__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubAdminSuggestionApiView(APIView):
    """
    Sub Admin Suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []
            users = Users.objects.annotate(data=Concat('first_name', V(' '), 'last_name')).filter(network_user__domain=site_id, network_user__is_agent=1, data__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('email')).filter(network_user__domain=site_id, network_user__is_agent=1, email__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('phone_no')).filter(network_user__domain=site_id, network_user__is_agent=1, phone_no__icontains=search).values("data")
            searched_data = searched_data + list(users)

            # profile = UserBusinessProfile.objects.annotate(data=F('company_name')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, company_name__icontains=search).values("data")
            # searched_data = searched_data + list(profile)

            # profile = UserBusinessProfile.objects.annotate(data=F('licence_no')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, licence_no__icontains=search).values("data")
            # searched_data = searched_data + list(profile)

            # profile = UserBusinessProfile.objects.annotate(data=F('address_first')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, address_first__icontains=search).values("data")
            # searched_data = searched_data + list(profile)

            # profile = UserBusinessProfile.objects.annotate(data=F('postal_code')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, postal_code__icontains=search).values("data")
            # searched_data = searched_data + list(profile)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))            


class EmailValidationApiView(APIView):
    """
    Email validation suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            users = Users.objects.filter(email__iexact="Mac@mailinator.com")
            print(users)
            return Response(response.parsejson("Fetch data.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminContactUsListingApiView(APIView):
    """
    Contact us listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            contact_us = ContactUs.objects.filter(domain=site_id, domain__users_site_id__id=user_id)
            if 'user_type' in data and data['user_type'] != "":
                contact_us = contact_us.filter(Q(user_type__icontains=data['user_type']))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    contact_us = contact_us.filter(Q(id=search) | Q(phone_no=search))
                else:
                    contact_us = contact_us.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(user_type__icontains=search) | Q(full_name__icontains=search))
            total = contact_us.count()
            contact_us = contact_us.order_by("-id").only("id")[offset: limit]
            serializer = ContactUsListingSerializer(contact_us, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminContactUsDetailApiView(APIView):
    """
    Contact us detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "contact_id" in data and data['contact_id'] != "":
                contact_id = int(data['contact_id'])
            else:
                return Response(response.parsejson("contact_id is required", "", status=403))

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            contact_us = ContactUs.objects.get(id=contact_id, domain=site_id, domain__users_site_id__id=user_id)
            serializer = ContactUsListingSerializer(contact_us)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainArticleSuggestionApiView(APIView):
    """
    Subdomain article suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            network_article = NetworkArticles.objects.annotate(data=F('title')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(network_article)

            network_article = NetworkArticles.objects.annotate(data=F('asset__name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(network_article)

            network_article = NetworkArticles.objects.annotate(data=F('author_name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(network_article)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetExpertiseIconApiView(APIView):
    """
    Get expertise icon
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "icon_type" in data and data['icon_type'] != "":
                icon_type = int(data['icon_type'])
            else:
                return Response(response.parsejson("icon_type is required", "", status=403))

            icon = ExpertiseIcon.objects.filter(icon_type=icon_type, status=1).values('id', 'icon_name')
            return Response(response.parsejson("Fetch data.", icon, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserProfileDetailApiView(APIView):
    """
    User profile detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, site=site_id, status=1, user_type__in=[1, 2]).first()
                if user is None:
                    user = Users.objects.filter(id=user_id, status=1, network_user__domain=site_id, user_type__in=[1, 2]).first()
                    if user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            users = Users.objects.get(id=user_id)
            serializer = UserProfileDetailSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserProfileUpdateApiView(APIView):
    """
    User profile update
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, site=site_id, status=1, user_type__in=[1, 2]).first()
                if user is None:
                    user = Users.objects.filter(id=user_id, status=1, network_user__domain=site_id, user_type__in=[1, 2]).first()
                    if user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
                described_by = user.described_by
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "first_name" in data and data['first_name'] != "":
                first_name = data['first_name']
            else:
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" in data and data['last_name'] != "":
                last_name = data['last_name']
            else:
                return Response(response.parsejson("last_name is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
                users = Users.objects.filter(email__iexact=email).exclude(id=user_id).first()
                if users is not None:
                    # Translators: This message appears when email already in db
                    return Response(response.parsejson("Email already exist", "", status=403))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" in data and data['phone_no'] != "":
                phone_no = data['phone_no']
                # users = Users.objects.filter(phone_no=phone_no).exclude(id=user_id).first()
                # if users is not None:
                #     # Translators: This message appears when phone number already in db
                #     return Response(response.parsejson("Phone number already exist", "", status=403))
            else:
                return Response(response.parsejson("phone_no is required", "", status=403))
            profile_image = None
            if "profile_image" in data and data['profile_image'] != "":
                profile_image = int(data['profile_image'])

            if "address" in data and type(data['address']) == dict and len(data['address']) > 0:
                address = data['address']
                if "address_first" in address and address["address_first"] != "":
                    address_first = address["address_first"]
                else:
                    return Response(response.parsejson("address->address_first is required", "", status=403))

                if "state" in address and address["state"] != "":
                    state = int(address["state"])
                else:
                    return Response(response.parsejson("address->state is required", "", status=403))

                if "postal_code" in address and address["postal_code"] != "":
                    postal_code = address["postal_code"]
                else:
                    return Response(response.parsejson("address->postal_code is required", "", status=403))

                if "city" in address and address["city"] != "":
                    city = address["city"]
                else:
                    return Response(response.parsejson("address->city is required", "", status=403))

                if "country" in address and address["country"] != "":
                    country = int(address["country"])
                else:
                    return Response(response.parsejson("address->country is required", "", status=403))
            else:
                return Response(response.parsejson("address is required", "", status=403))

            brokerage_name = None
            licence_number = None
            if described_by is not None and described_by == 3:
                if "brokerage_name" in data and data["brokerage_name"] != "":
                    brokerage_name = data["brokerage_name"]

                if "licence_number" in data and data["licence_number"] != "":
                    licence_number = data["licence_number"]

            users = Users.objects.get(id=user_id)
            users.first_name = first_name
            users.last_name = last_name
            users.email = email
            users.phone_no = phone_no
            users.profile_image = profile_image
            users.save()
            profile_address = ProfileAddress.objects.filter(user=user_id, address_type=1, status=1).first()
            if profile_address is None:
                profile_address = ProfileAddress()
                profile_address.user_id = user_id
                profile_address.address_type_id = 1
                profile_address.status_id = 1
                profile_address.added_by_id = user_id
                profile_address.updated_by_id = user_id
            profile_address.address_first = address_first
            profile_address.country_id = country
            profile_address.state_id = state
            profile_address.postal_code = postal_code
            profile_address.city = city
            profile_address.save()

            if described_by is not None and described_by == 3:
                network_user = NetworkUser.objects.filter(domain=site_id, user=user_id).first()
                network_user.brokerage_name = brokerage_name
                network_user.licence_number = licence_number
                network_user.save()
            return Response(response.parsejson("Profile updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontUserChangePasswordApiView(APIView):
    """
    Front user change Password
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, site=site_id, status=1, user_type__in=[1, 2]).first()
                if user is None:
                    user = Users.objects.filter(id=user_id, status=1, network_user__domain=site_id, user_type__in=[1, 2]).first()
                    if user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                # Translators: This message appears when password is empty
                return Response(response.parsejson("password is required", "", status=403))

            if "new_password" in data and data['new_password'] != "":
                new_password = data['new_password']
            else:
                # Translators: This message appears when new_password is empty
                return Response(response.parsejson("new_password is required", "", status=403))

            if password == new_password:
                return Response(response.parsejson("New password should be different from old password.", "", status=403))

            if not check_password(password, user.password):
                # Translators: This message appears when password not match
                return Response(response.parsejson("Current password not matched", "", status=403))

            # This is required for Oauth
            user.encrypted_password = b64encode(new_password)
            user.password = make_password(new_password)
            user.save()
            #send Email =======================
            user_data = Users.objects.get(id=user_id)
            user_name = user_data.first_name if user_data.first_name is not None else ""
            user_email = user_data.email if user_data.email is not None else ""
            admin_data = Users.objects.get(site_id=site_id)
            admin_name = admin_data.first_name if admin_data.first_name is not None else ""
            admin_email = admin_data.email if admin_data.email is not None else ""
            domain_name = network.domain_name
            template_data = {"domain_id": site_id, "slug": "user_change_password"}
            extra_data = {
                "user_name": user_name,
                "user_email": user_email,
                "password": new_password,
                "name": admin_name,
                "email": admin_email,
                "domain_name": domain_name.title(),
                "domain_id": site_id  
            }
            compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Password successfully changed.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AgentListApiView(APIView):
    """
    Agent listing
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]
    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            network_user = NetworkUser.objects.filter(domain=site_id, is_agent=1, status=1)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_user = network_user.filter(Q(id=search))
                else:
                    network_user = network_user.annotate(full_name=Concat('user__user_business_profile__first_name', V(' '), 'user__user_business_profile__last_name')).filter(Q(user__user_business_profile__phone_no__icontains=search) | Q(user__user_business_profile__email__icontains=search) | Q(user__user_business_profile__licence_no__icontains=search) | Q(user__user_business_profile__company_name__icontains=search) | Q(full_name__icontains=search))
            total = network_user.count()
            network_user = network_user.order_by("-id").only('id')[offset: limit]
            serializer = AgentListSerializer(network_user, many=True)
            all_data = {}
            all_data['data'] = serializer.data
            all_data['total'] = total
            return Response(response.parsejson("Fetch Data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AgentSearchSuggestionApiView(APIView):
    """
    Agent search suggestion
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []
            users = Users.objects.annotate(data=Concat('user_business_profile__first_name', V(' '), 'user_business_profile__last_name')).filter(network_user__domain=site_id, network_user__is_agent=1, data__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('user_business_profile__email')).filter(network_user__domain=site_id, network_user__is_agent=1, user_business_profile__email__icontains=search).values("data")
            searched_data = searched_data + list(users)

            users = Users.objects.annotate(data=F('user_business_profile__phone_no')).filter(network_user__domain=site_id, network_user__is_agent=1, user_business_profile__phone_no__icontains=search).values("data")
            searched_data = searched_data + list(users)

            profile = UserBusinessProfile.objects.annotate(data=F('company_name')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, company_name__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            profile = UserBusinessProfile.objects.annotate(data=F('licence_no')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, licence_no__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            profile = UserBusinessProfile.objects.annotate(data=F('company_name')).filter(user__network_user__domain=site_id, user__network_user__is_agent=1, company_name__icontains=search).values("data")
            searched_data = searched_data + list(profile)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainUserRegistrationApiView(APIView):
    """
    Subdomain user registration
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__status=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))

                image = {}
                if users.profile_image is not None and users.profile_image != "":
                    profile_image = UserUploads.objects.filter(id=int(users.profile_image), is_active=1).last()
                    if profile_image is not None:
                        image = {"doc_file_name": profile_image.doc_file_name, "bucket_name": profile_image.bucket_name}

                user_detail = {
                    "first_name": users.first_name,
                    "last_name": users.last_name,
                    "email": users.email,
                    "phone_no": users.phone_no,
                    "profile_image": image
                }
                profile_address = ProfileAddress.objects.filter(user=user_id, address_type__in=[1]).first()
                if profile_address is not None:
                    user_detail['address_first'] = profile_address.address_first
                    user_detail['address_second'] = profile_address.address_second
                    user_detail['city'] = profile_address.city
                    user_detail['state_name'] = profile_address.state.state_name
                    user_detail['postal_code'] = profile_address.postal_code
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            bid_registration = BidRegistration.objects.filter(domain=site_id, user=user_id, status=1)
            total = bid_registration.count()
            bid_registration = bid_registration.order_by("-id").only("id")[offset: limit]

            serializer = SubdomainUserRegistrationSerializer(bid_registration, many=True)
            all_data = {
                "data": serializer.data,
                "total": total,
                "user_detail": user_detail
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AgentListingApiView(APIView):
    """
    Agent listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                except_user = None
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != domain_id:
                    except_user = user_id
                    network_user = NetworkUser.objects.filter(domain=domain_id, user=user_id, status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            users = Users.objects.filter(network_user__domain=domain_id, user_type=2, network_user__is_agent=1).exclude(id=except_user)
            users = users.values("id", "first_name", "last_name", "email").order_by("-network_user__id")
            return Response(response.parsejson("Fetch data.", users, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendCustomEmailApiView(APIView):
    """
    Send custom email
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                if is_super_admin is None:
                    user = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                    if user is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    elif user.site_id != domain_id:
                        network_user = NetworkUser.objects.filter(domain=domain_id, user=user_id, status=1, is_agent=1).first()
                        if network_user is None:
                            return Response(response.parsejson("Not site user.", "", status=201))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "email_for" in data and data['email_for'] != "":
                email_for = data['email_for']
            else:
                return Response(response.parsejson("email_for is required", "", status=403))

            if "subject" in data and data['subject'] != "":
                subject = data['subject']
            else:
                return Response(response.parsejson("subject is required", "", status=403))

            if "message" in data and data['message'] != "":
                message = data['message']
            else:
                return Response(response.parsejson("message is required", "", status=403))
            is_bidder = False
            if email_for == "total_bids":
                slug = "total_bids"
                bid = Bid.objects.values("user", email=F("user__email")).annotate(bids=Count("user")).filter(Q(domain=domain_id) & Q(property=property_id) & Q(is_canceled=0))
                to_email = [email_data['email'] for email_data in bid]
                to_email = list(set(to_email))
            elif email_for == "watching":
                slug = "watching"
                watching = PropertyWatcher.objects.filter(property=property_id, user__isnull=False)
                to_email = [email_data.user.email for email_data in watching]
                to_email = list(set(to_email))
            elif email_for == "property_viewer":
                slug = "property_viewer"
                property_view = PropertyView.objects.filter(property=property_id)
                to_email = [viewer.user.email for viewer in property_view]
                to_email = list(set(to_email))
            elif email_for == "bidder":
                slug = "total_bids"
                bid = BidRegistrationAddress.objects.filter(registration__property=property_id, address_type__in=[2, 3], registration__bid_registration_bid__id__gt=0, status=1)
                to_email = [email_data.email for email_data in bid]
                to_email = list(set(to_email))
                is_bidder = True

            notification_template = NotificationTemplate.objects.filter(Q(event__slug=slug) & Q(site=domain_id) & Q(status=1)).first()
            if notification_template is None:
                notification_template = NotificationTemplate.objects.filter(Q(event__slug=slug) & Q(site__isnull=True) & Q(status=1)).first()

            if notification_template is not None:
                # Get property data property_id
                proeprty_data = PropertyListing.objects.get(id=property_id)
                auction_type = proeprty_data.sale_by_type.auction_type
                auction_data = PropertyAuction.objects.get(property=property_id)
                start_price = auction_data.start_price
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                property_link = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(property_id)
                property_address = proeprty_data.address_one
                property_city = proeprty_data.city
                property_state = proeprty_data.state.state_name
                asset_type = proeprty_data.property_asset.name 
                for email in to_email:
                    if is_bidder:
                        user_data = BidRegistrationAddress.objects.filter(email=email).first()
                        name = user_data.first_name
                    else:
                        user_data = Users.objects.get(email=email)
                        name = user_data.first_name
                    template_data = {"domain_id": domain_id, "slug": slug}
                    extra_data = {'message': message,
                                  'name': name,
                                  'property_link': property_link,
                                  'property_image': image_url,
                                  'property_address': property_address,
                                  'property_city': property_city,
                                  'property_state': property_state,
                                  'auction_type': auction_type,
                                  'asset_type': asset_type,
                                  'starting_price': number_format(start_price),
                                  'subject': subject,
                                  "domain_id": domain_id
                                  }
                    compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
                return Response(response.parsejson("Email sent successfully.", "", status=201))
            else:
                return Response(response.parsejson("Email not sent.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanBillingDetailApiView(APIView):
    """
    Plan billing detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, user_type=2, status=1, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("User not exist", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "subscription_id" in data and data['subscription_id'] != "":
                subscription_id = int(data['subscription_id'])
            else:
                return Response(response.parsejson("subscription_id is required", "", status=403))

            user_subscription = UserSubscription.objects.filter(id=subscription_id, domain=site_id, user__site=site_id).first()
            serializer = PlanBillingDetailSerializer(user_subscription)
            all_data = {
                "data": serializer.data,
            }
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChangeThemeApiView(APIView):
    """
    Change Theme
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = int(data['user'])
                users = Users.objects.filter(id=user, site=domain, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("You can't update theme.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "theme" in data and data['theme'] != "":
                theme = int(data['theme'])
                theme = ThemesAvailable.objects.filter(id=theme, is_active=1).first()
                current_theme = theme.theme_name
                if theme is None:
                    return Response(response.parsejson("Theme not available", "", status=403))
            else:
                return Response(response.parsejson("theme is required", "", status=403))
            old_theme = UserTheme.objects.filter(domain=domain, status=1).last()
            if old_theme.theme_id == int(data['theme']):
                return Response(response.parsejson("This theme is your current theme.", "", status=403))
            # -----------------Theme selection------------
            data['status'] = 1
            serializer = UserThemeSerializer(data=data)
            if serializer.is_valid():
                data = serializer.save()

                try:
                    updated_theme = data.theme.theme_name
                    #  send change theme email
                    # if current_theme != updated_theme:
                    site_setting = SiteSetting.objects.filter(settings_name="Admin Email").first()
                    user_name = users.first_name if users.first_name is not None else ""
                    user_email = users.email if users.email is not None else ""
                    template_data = {"domain_id": domain, "slug": "theme_change"}
                    extra_data = {
                        "user_name": user_name,
                        "theme_name": updated_theme,
                        "domain_id": domain,
                        "email": site_setting.setting_value
                    }
                    compose_email(to_email=[user_email], template_data=template_data, extra_data=extra_data)
                except:
                    pass
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Theme updated successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PasswordVerifyApiView(APIView):
    """
    Password verify
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "password" in data and data['password'] != "":
                password = data['password']
            else:
                return Response(response.parsejson("password is required", "", status=403))
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if not check_password(password, users.password):
                return Response(response.parsejson("Wrong Password", "", status=403))
            return Response(response.parsejson("Password successfully validated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetPlanApiView(APIView):
    """
    Get Plan
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))
            user_subscription = UserSubscription.objects.filter(domain=domain).last()
            plan_id = user_subscription.opted_plan.subscription_id
            users = Users.objects.get(site=domain)
            data = {"plan_id": plan_id, "user_id": users.id}
            return Response(response.parsejson("Fetch Data.", data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendResetPasswordLinkApiView(APIView):
    """
    Send Reset Password Link
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                domain_url = network.domain_url
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                users = Users.objects.filter(id=user_id).first()
                if users is None:
                    # Translators: This message appears when email not matched with user
                    return Response(response.parsejson("User Not exist.", "", status=403))
                if users.status_id != 1:
                    # Translators: This message appears when user is not active
                    return Response(response.parsejson("User is blocked or deleted.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            # ===================Inactive all exist user token================
            UserPasswordReset.objects.filter(user=users.id).update(is_active=0)
            reset_token = forgot_token()
            if not reset_token:
                return Response(response.parsejson("Getting Some Issue.", "", status=403))

            # Token entry
            user_password_reset = UserPasswordReset()
            user_password_reset.user_id = users.id
            user_password_reset.reset_token = reset_token
            user_password_reset.is_active = 1
            user_password_reset.added_by_id = users.id
            user_password_reset.save()
            reset_link = domain_url+"reset-password/?token="+str(reset_token)
            # ------------------------Email-----------------------
            extra_data = {"user_name": users.first_name, "reset_link": reset_link, 'web_url': settings.FRONT_BASE_URL, "domain_id": domain_id}
            template_data = {"domain_id": domain_id, "slug": "reset_forgot_password_link"}
            compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Password reset link sent successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetCurrentPlanApiView(APIView):
    """
    Get Current Plan
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))
            user_subscription = UserSubscription.objects.filter(domain=domain).last()
            plan_id = user_subscription.opted_plan.subscription_id
            users = Users.objects.get(site=domain)
            data = {"plan_id": plan_id, "user_id": users.id, "is_free": user_subscription.opted_plan.subscription.is_free}
            return Response(response.parsejson("Fetch Data.", data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddTestimonialApiView(APIView):
    """
    Add/Update testimonial
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            testimonial_id = None
            if "testimonial_id" in data and data['testimonial_id'] != "":
                testimonial_id = int(data['testimonial_id'])
                testimonial_id = NetworkTestimonials.objects.get(id=testimonial_id)
            required_field = ["description", "author_name", "status", "user_id", "type"]
            for field in required_field:
                if field in data and data[field] != "":
                    field = data[field]
                else:
                    return Response(response.parsejson(field + " is required", "", status=403))

            if "author_image" in data and data['author_image'] != "":
                author_image = int(data['author_image'])
            else:
                data['author_image'] = None
            data['added_by'] = data['user_id']
            data['updated_by'] = data['user_id']
            serializer = AddTestimonialSerializer(testimonial_id, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                # copy_errors.update(user_profile_serializer.errors)
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Testimonial successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TestimonialListingApiView(APIView):
    """
    Testimonial listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            network_testimonials = NetworkTestimonials.objects.filter(domain=site_id)
            if "status" in data and data["status"] != "":
                network_testimonials = network_testimonials.filter(status__in=data["status"])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search']
                if search.isdigit():
                    network_testimonials = network_testimonials.filter(Q(id=search))
                else:
                    network_testimonials = network_testimonials.filter(Q(author_name__icontains=search) | Q(type__icontains=search))

            total = network_testimonials.count()
            network_testimonials = network_testimonials.order_by("-id").only("id")[offset:limit]
            serializer = TestimonialsListingSerializer(network_testimonials, many=True)
            all_data = {"total": total, "data": serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NewCheckSubdomainApiView(APIView):
    """
    New Check subdomain
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip()
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            domain_name = "https://" + domain_name

            network_domain = NetworkDomain.objects.filter(domain_url=domain_name, is_active=1, is_delete=False).first()
            all_data = {"domain_name": False}
            if network_domain is not None:
                all_data["domain_name"] = True
                all_data["site_id"] = network_domain.id
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class NewSettingsDataApiView(APIView):
    """
    New Settings Data
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip()
                domain_name = "https://" + domain_name
                # network = NetworkDomain.objects.filter(domain_name=domain_name, is_active=1).first()
                network = NetworkDomain.objects.filter(domain_url=domain_name, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                site_id = network.id
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif users.site_id != site_id:
                    network_user = NetworkUser.objects.filter(user=user_id, domain=site_id, status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User not registered for this domain.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            users = Users.objects.filter(id=user_id, status=1).first()
            serializer = SettingsDataSerializer(users, context=site_id)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TestimonialDetailApiView(APIView):
    """
    Testimonial detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "testimonial_id" in data and data['testimonial_id'] != "":
                testimonial_id = int(data['testimonial_id'])
            else:
                return Response(response.parsejson("testimonial_id is required", "", status=403))

            network_testimonials = NetworkTestimonials.objects.get(id=testimonial_id, domain=site_id)
            serializer = TestimonialDetailSerializer(network_testimonials)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontTestimonialApiView(APIView):
    """
    Front Testimonial
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "type" in data and data['type'] != "":
                type = data['type'].lower()
            else:
                return Response(response.parsejson("type is required", "", status=403))

            network_testimonials = NetworkTestimonials.objects.filter(domain=site_id, type=type, status=1)
            serializer = FrontTestimonialSerializer(network_testimonials, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TestimonialImageDeleteApiView(APIView):
    """
    Testimonial Image Delete
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != site_id:
                    network_user = NetworkUser.objects.filter(domain=site_id, user=user_id, is_agent=1,
                                                              status=1).first()
                    if network_user is None:
                        return Response(response.parsejson("User is not broker/agent.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            testimonial_id = None
            if "testimonial_id" in data and data['testimonial_id'] != "":
                testimonial_id = int(data['testimonial_id'])

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            with transaction.atomic():
                try:
                    if testimonial_id is not None:
                        NetworkTestimonials.objects.filter(id=testimonial_id).update(author_image=None)
                    UserUploads.objects.filter(id=upload_id).delete()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Success.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainTestimonialsSuggestionApiView(APIView):
    """
    Subdomain testimonials suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            network_testimonials = NetworkTestimonials.objects.annotate(data=F('type')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(network_testimonials)

            network_testimonials = NetworkTestimonials.objects.annotate(data=F('author_name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(network_testimonials)

            # network_testimonials = NetworkTestimonials.objects.annotate(data=F('author_name')).filter(domain=site_id, data__icontains=search).values("data")
            # searched_data = searched_data + list(network_testimonials)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FreeSubscriptionEndCronApiView(APIView):
    """
    Free Subscription End Cron
    """
    # authentication_classes = [OAuth2Authentication]
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request):
        try:
            # now = timezone.now()
            # user_subscription = UserSubscription.objects.filter(is_first_subscription=1, is_free=False, end_date__lte=now).order_by("-id")
            # for subscription in user_subscription:
            #     UserSubscription.objects.filter(id=subscription.id).update(opted_plan=settings.FREE_PLAN_ID, is_free=True, is_first_subscription=0, previous_plan_id=subscription.opted_plan)
            #     permission = [5, 7]
            #     UserPermission.objects.filter(domain=subscription.domain_id, user=subscription.user_id).update(is_permission=0)
            #     for permission_data in permission:
            #         user_permission = UserPermission()
            #         user_permission.domain_id = subscription.domain_id
            #         user_permission.user_id = subscription.user_id
            #         user_permission.permission_id = permission_data
            #         user_permission.is_permission = 1
            #         user_permission.save()
            return Response(response.parsejson("Fetch data.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UserRegisteredDomainApiView(APIView):
    """
    User Registered Domain
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            network_user = NetworkUser.objects.filter(user=user_id).values("domain__id", "domain__domain_name", "domain__domain_url")
            return Response(response.parsejson("Fetch data.", list(network_user), status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AccountActivationEmailApiView(APIView):
    """
    Free Subscription End Cron
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            user = Users.objects.filter(id=user_id).first()
            # ------------------------Email-----------------------
            activation_link = settings.RESET_PASSWORD_URL + "/activation/?token=" + str(user.activation_code)
            template_data = {"domain_id": "", "slug": "default_welcome"}
            admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
            admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
            admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
            admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
            extra_data = {"user_name": user.first_name,
                          "activation_link": activation_link,
                          "web_url": settings.FRONT_BASE_URL,
                          "user_type": "Agent/Broker",
                          "domain_name": "Bidhom",
                          "user_email": user.email,
                          "user_password": user.phone_no,
                          "admin_name": admin_name,
                          "admin_email": admin_email,
                          "sub_domain": user.site.domain_name,
                          "domain_url": user.site.domain_url
                          }
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Activation email sent successfully to "+ user.email+".", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TempDataApiView(APIView):
    """
    Temp Data
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    # @transaction.atomic
    @staticmethod
    def post(request):
        try:
            data = request.data
            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            temp_user = TempRegistration.objects.filter(email=email).order_by("-id").values('id', 'email', 'first_name', 'last_name', 'phone_no')[0: 1]
            return Response(response.parsejson("Fetch Data", temp_user, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class TempRegistrationCronApiView(APIView):
    """
    Temp Registration Cron
    """
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request):
        try:
            now = timezone.now()
            temp_user = TempRegistration.objects.filter(is_active=1)
            # ----------------Check Email In Users Table----------------
            for user in temp_user:
                users = Users.objects.filter(email=user.email).first()
                if users is not None:
                    user.is_business_email_send = 1
                    user.is_active = 0
                    user.save()

            temp_user = TempRegistration.objects.filter(is_business_email_send=0)
            # ----------------Email To Business Team----------------
            for user in temp_user:
                user.is_business_email_send = 1
                user.save()
                # ------------------------Email-----------------------
                template_data = {"domain_id": "", "slug": "business_registration_reminder"}
                admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
                admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
                admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
                admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
                extra_data = {"user_name": user.first_name,
                              "web_url": settings.FRONT_BASE_URL,
                              "user_type": "Agent/Broker",
                              "domain_name": "Bidhom",
                              "first_name": user.first_name,
                              "last_name": user.last_name,
                              "user_email": user.email,
                              "phone_no": user.phone_no,
                              "admin_name": admin_name,
                              "admin_email": admin_email,
                              }
                # compose_email(to_email=[''], template_data=template_data, extra_data=extra_data)

            # ----------------Email To Registration Pending Users----------------
            temp_user = TempRegistration.objects.filter(added_on__date__lt=now, is_active=1)
            for user in temp_user:
                user.is_active = 0
                user.save()
                # ------------------------Email-----------------------
                registration_link = settings.RESET_PASSWORD_URL + "/register/?email=" + str(user.email)
                template_data = {"domain_id": "", "slug": "registration_reminder"}
                admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
                admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
                admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
                admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
                extra_data = {"user_name": user.first_name,
                              "registration_link": registration_link,
                              "web_url": settings.FRONT_BASE_URL,
                              "user_type": "Agent/Broker",
                              "domain_name": "Bidhom",
                              "first_name": user.first_name,
                              "last_name": user.last_name,
                              "user_email": user.email,
                              "phone_no": user.phone_no,
                              "admin_name": admin_name,
                              "admin_email": admin_email,
                              }
                compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Success", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminDashboardApiView(APIView):
    """
    Admin dashboard
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            start_date = None
            if "start_date" in data and data['start_date'] != "":
                start_date = data['start_date']

            end_date = None
            if "end_date" in data and data['end_date'] != "":
                end_date = data['end_date']

            today_date = datetime.date.today()
            start_year = today_date.year

            # Calculate total offer here
            master_offer = MasterOffer.objects.filter(domain=site_id).exclude(status=5)

            # Calculate total registration
            bid_registration = BidRegistration.objects.filter(domain=site_id).exclude(status__in=[2, 5])

            # Calculate total customer
            customer = NetworkUser.objects.filter(domain=site_id, is_agent=0, user__status__in=[1, 2])

            # Calculate total agent
            agent = NetworkUser.objects.filter(domain=site_id, is_agent=1, user__status__in=[1, 2])

            # Calculate total property
            listing = PropertyListing.objects.filter(domain=site_id).exclude(status=5)

            # Calculate total sold property
            sold_listing = PropertyListing.objects.filter(domain=site_id, status=9)

            # Calculate total boat
            boat = PropertyEvaluatorDomain.objects.filter(domain=site_id)

            # Calculate total inquiry
            contact_us = ContactUs.objects.filter(domain=site_id)

            if start_date is not None and end_date is not None:
                master_offer = master_offer.filter(added_on__range=(start_date, end_date))
                bid_registration = bid_registration.filter(added_on__range=(start_date, end_date))
                customer = customer.filter(added_on__range=(start_date, end_date))
                agent = agent.filter(added_on__range=(start_date, end_date))
                listing = listing.filter(added_on__range=(start_date, end_date))
                sold_listing = sold_listing.filter(added_on__range=(start_date, end_date))
                boat = boat.filter(added_on__range=(start_date, end_date))
                contact_us = contact_us.filter(added_on__range=(start_date, end_date))
            elif start_date is not None and end_date is None:
                master_offer = master_offer.filter(added_on__gte=start_date)
                bid_registration = bid_registration.filter(added_on__gte=start_date)
                customer = customer.filter(added_on__gte=start_date)
                agent = agent.filter(added_on__gte=start_date)
                listing = listing.filter(added_on__gte=start_date)
                sold_listing = sold_listing.filter(added_on__gte=start_date)
                boat = boat.filter(added_on__gte=start_date)
                contact_us = contact_us.filter(added_on__gte=start_date)
            elif end_date is not None and start_date is None:
                master_offer = master_offer.filter(added_on__lte=end_date)
                bid_registration = bid_registration.filter(added_on__lte=end_date)
                customer = customer.filter(added_on__lte=end_date)
                agent = agent.filter(added_on__lte=end_date)
                listing = listing.filter(added_on__lte=end_date)
                sold_listing = sold_listing.filter(added_on__lte=end_date)
                boat = boat.filter(added_on__lte=end_date)
                contact_us = contact_us.filter(added_on__lte=end_date)
            else:
                master_offer = master_offer.filter(added_on__year=start_year)
                bid_registration = bid_registration.filter(added_on__year=start_year)
                customer = customer.filter(added_on__year=start_year)
                agent = agent.filter(added_on__year=start_year)
                listing = listing.filter(added_on__year=start_year)
                sold_listing = sold_listing.filter(added_on__year=start_year)
                boat = boat.filter(added_on__year=start_year)
                contact_us = contact_us.filter(added_on__year=start_year)

            total_offer_received = master_offer.count()
            total_register_user = bid_registration.count()
            total_customer = customer.count()
            total_agent = agent.count()
            total_property = listing.count()
            total_sold_property = sold_listing.count()
            total_boat_request = boat.count()
            total_enquiry = contact_us.count()
            total_data = {"total_offer_received": total_offer_received,
                          "total_register_user": total_register_user,
                          "total_customer": total_customer,
                          "total_agent": total_agent,
                          "total_property": total_property,
                          "total_sold_property": total_sold_property,
                          "total_boat_request": total_boat_request,
                          "total_enquiry": total_enquiry}

            return Response(response.parsejson("Fetch data.", total_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyRegistrationGraphApiView(APIView):
    """
    Property Registration Graph
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            start_date = None
            start_month = 1
            if "start_date" in data and data['start_date'] != "":
                start_date = data['start_date']
                start_month = int(start_date.split("-")[1])

            end_date = None
            if "end_date" in data and data['end_date'] != "":
                end_date = data['end_date']

            today_date = datetime.date.today()
            today_date = datetime.date.today()
            start_year = today_date.year
            end_year = None

            # property = PropertyListing.objects.filter(domain=site_id, added_on__year=today_date.year).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
            # bid_registration = BidRegistration.objects.filter(domain=site_id, added_on__year=today_date.year).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
            # if start_date is not None and end_date is not None:
            #     property = property.filter(added_on__range=(start_date, end_date))
            #     bid_registration = bid_registration.filter(added_on__range=(start_date, end_date))
            # elif start_date is not None and end_date is None:
            #     property = property.filter(added_on__gte=start_date)
            #     bid_registration = bid_registration.filter(added_on__gte=start_date)
            #
            # elif end_date is not None and start_date is None:
            #     property = property.filter(added_on__lte=end_date)
            #     bid_registration = bid_registration.filter(added_on__lte=end_date)
            if start_date is not None and end_date is not None:
                start_year_data = start_date.split("-")
                start_year_data = int(start_year_data[0])

                end_year_data = end_date.split("-")
                end_year_data = int(end_year_data[0])

                if start_year_data == end_year_data:
                    start_year = start_year_data
                elif start_year_data != end_year_data:
                    start_year = start_year_data
                    end_year = end_year_data

            if start_year is not None and end_year is not None:
                property = PropertyListing.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).exclude(status=5).annotate(production_month=TruncYear('added_on')).values('production_month', 'added_on__year').annotate(count=Count('id')).order_by('production_month')
                bid_registration = BidRegistration.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).exclude(status__in=[2, 5]).annotate(production_month=TruncYear('added_on')).values('production_month', 'added_on__year').annotate(count=Count('id')).order_by('production_month')
                monthly_counts = {month: 0 for month in range(start_year, end_year+1)}
                for property_detail in property:
                    month = property_detail['production_month'].year
                    count = property_detail['count']
                    monthly_counts[month] = count
                property_data_display = [i for i in monthly_counts.values()]

                monthly_counts_registration = {month: 0 for month in range(start_year, end_year+1)}
                for registration in bid_registration:
                    month = registration['production_month'].year
                    count = registration['count']
                    monthly_counts_registration[month] = count
                registration_data_display = [i for i in monthly_counts_registration.values()]
            else:
                if start_date is not None and end_date is not None:
                    property = PropertyListing.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).exclude(status=5).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                    bid_registration = BidRegistration.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).exclude(status__in=[2, 5]).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                else:
                    property = PropertyListing.objects.filter(domain=site_id, added_on__year=start_year).exclude(status=5).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                    bid_registration = BidRegistration.objects.filter(domain=site_id, added_on__year=start_year).exclude(status__in=[2, 5]).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')

                monthly_counts = {month: 0 for month in range(start_month, 13)}
                for property_detail in property:
                    month = property_detail['production_month'].month
                    count = property_detail['count']
                    monthly_counts[month] = count
                property_data_display = [i for i in monthly_counts.values()]

                monthly_counts_registration = {month: 0 for month in range(start_month, 13)}
                for registration in bid_registration:
                    month = registration['production_month'].month
                    count = registration['count']
                    monthly_counts_registration[month] = count
                registration_data_display = [i for i in monthly_counts_registration.values()]
            total_data = {"property_data_display": property_data_display, "registration_data_display": registration_data_display}
            return Response(response.parsejson("Fetch data.", total_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SignupPageGraphApiView(APIView):
    """
    Signup Page Graph
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            start_date = None
            start_month = 1
            if "start_date" in data and data['start_date'] != "":
                start_date = data['start_date']
                start_month = int(start_date.split("-")[1])

            end_date = None
            if "end_date" in data and data['end_date'] != "":
                end_date = data['end_date']

            today_date = datetime.date.today()
            start_year = today_date.year
            end_year = None

            # users = NetworkUser.objects.filter(domain=site_id, added_on__year=today_date.year).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
            # property_view = PropertyView.objects.filter(domain=site_id, added_on__year=today_date.year).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')

            if start_date is not None and end_date is not None:
                start_year_data = start_date.split("-")
                start_year_data = int(start_year_data[0])

                end_year_data = end_date.split("-")
                end_year_data = int(end_year_data[0])

                if start_year_data == end_year_data:
                    start_year = start_year_data
                elif start_year_data != end_year_data:
                    start_year = start_year_data
                    end_year = end_year_data

                # users = users.filter(added_on__range=(start_date, end_date))
                # property_view = property_view.filter(added_on__range=(start_date, end_date))
            if start_year is not None and end_year is not None:
                users = NetworkUser.objects.filter(domain=site_id, is_agent=0, added_on__range=(start_date, end_date), user__status__in=[1, 2]).annotate(production_month=TruncYear('added_on')).values('production_month', 'added_on__year').annotate(count=Count('id')).order_by('production_month')
                property_view = PropertyView.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).annotate(production_month=TruncYear('added_on')).values('production_month', 'added_on__year').annotate(count=Count('id')).order_by('production_month')
                monthly_counts = {month: 0 for month in range(start_year, end_year+1)}
                for user in users:
                    month = user['production_month'].year
                    count = user['count']
                    monthly_counts[month] = count
                signup_data_display = [i for i in monthly_counts.values()]

                property_view_data = {month: 0 for month in range(start_year, end_year+1)}
                for registration in property_view:
                    month = registration['production_month'].year
                    count = registration['count']
                    property_view_data[month] = count
                property_view_display = [i for i in property_view_data.values()]
            else:
                if start_date is not None and end_date is not None:
                    users = NetworkUser.objects.filter(domain=site_id, is_agent=0, added_on__range=(start_date, end_date), user__status__in=[1, 2]).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                    property_view = PropertyView.objects.filter(domain=site_id, added_on__range=(start_date, end_date)).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                else:
                    users = NetworkUser.objects.filter(domain=site_id, is_agent=0, added_on__year=start_year, user__status__in=[1, 2]).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                    property_view = PropertyView.objects.filter(domain=site_id, added_on__year=start_year).annotate(production_month=TruncMonth('added_on')).values('production_month', 'added_on__month').annotate(count=Count('id')).order_by('production_month')
                monthly_counts = {month: 0 for month in range(start_month, 13)}
                for user in users:
                    month = user['production_month'].month
                    count = user['count']
                    monthly_counts[month] = count
                signup_data_display = [i for i in monthly_counts.values()]

                property_view_data = {month: 0 for month in range(start_month, 13)}
                for registration in property_view:
                    month = registration['production_month'].month
                    count = registration['count']
                    property_view_data[month] = count
                property_view_display = [i for i in property_view_data.values()]
            total_data = {"signup_data_display": signup_data_display, "page_view": property_view_display}
            return Response(response.parsejson("Fetch data.", total_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateDashboardMapApiView(APIView):
    """
    Update Dashboard Map
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            start_date = None
            if "start_date" in data and data['start_date'] != "":
                start_date = data['start_date']

            end_date = None
            if "end_date" in data and data['end_date'] != "":
                end_date = data['end_date']

            today_date = datetime.date.today()
            start_year = today_date.year

            property = PropertyListing.objects.filter(domain=site_id, added_on__year=start_year).exclude(status=5)

            # if start_date is not None and end_date is not None:
            #     property = property.filter(added_on__range=(start_date, end_date))
            # else:
            #     property = property.filter(added_on__year=start_year)
            property = property.only("id").order_by("-id")
            serializer = UpdateDashboardMapSerializer(property, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class EmailVerificationApiView(APIView):
    """
    Email Verification API
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "verification_code" in data and data['verification_code'] != "":
                verification_code = data['verification_code']
            else:
                # Translators: This message appears when verification_code is empty
                return Response(response.parsejson("verification_code is required", "", status=403))

            # users = Users.objects.filter(verification_code=verification_code, email_verified_on__isnull=True).first()
            users = Users.objects.filter(verification_code=verification_code).first()
            if users is None:
                return Response(response.parsejson("Data not found.", "", status=403))
            elif users is not None and users.email_verified_on is not None:
                return Response(response.parsejson("Email already verified.", "", status=403))

            users.email_verified_on = timezone.now()
            users.save()

            return Response(response.parsejson("Email Has Been Verified.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SendEmailVerificationLinkApiView(APIView):
    """
    Email Verification Link API
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']
            else:
                # Translators: This message appears when domain_id is empty
                return Response(response.parsejson("domain_id is required", "", status=403))

            users = Users.objects.filter(site_id=domain_id, status=1).first()
            verification_link = settings.RESET_PASSWORD_URL + "/email-verification/?token=" + str(users.verification_code)
            template_data = {"domain_id": "", "slug": "resend_email_verification_link"}
            admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
            admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
            admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
            admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
            extra_data = {"user_name": users.first_name,
                          "verification_link": verification_link,
                          "domain_name": "Bidhom",
                          "admin_name": admin_name,
                          "admin_email": admin_email,
                          }
            d = compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)
            msg = "Verification link sent <strong>successfully</strong> to <strong>" + users.email + "</strong>"
            return Response(response.parsejson(msg, "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminSendEmailVerificationLinkApiView(APIView):
    """
    Admin Send Email Verification Link
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))
            user = Users.objects.filter(id=user_id).first()
            # ------------------------Email-----------------------
            verification_link = settings.RESET_PASSWORD_URL + "/email-verification/?token=" + str(user.verification_code)
            template_data = {"domain_id": "", "slug": "resend_email_verification_link"}
            admin_settings_email = SiteSetting.objects.filter(id=1, is_active=1).first()
            admin_settings_name = SiteSetting.objects.filter(id=2, is_active=1).first()
            admin_name = admin_settings_name.setting_value if admin_settings_name is not None else ""
            admin_email = admin_settings_email.setting_value if admin_settings_email is not None else ""
            extra_data = {"user_name": user.first_name,
                          "verification_link": verification_link,
                          "domain_name": "Bidhom",
                          "admin_name": admin_name,
                          "admin_email": admin_email
                          }
            compose_email(to_email=[user.email], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Verification link sent successfully to "+ user.email+".", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetDomainUserDetailApiView(APIView):
    """
    Get Domain User Detail
    """
    authentication_classes = [TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "domain_name" in data and data['domain_name'] != "":
                domain_name = data['domain_name'].strip().lower()
            else:
                return Response(response.parsejson("domain_name is required", "", status=403))
            domain_name = "https://"+domain_name
            users = Users.objects.filter(site__domain_url=domain_name).last()
            serializer = GetDomainUserDetailSerializer(users)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DomainAssignPlanApiView(APIView):
    """
    Domain Assign Plan
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]
    # permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and len(data['domain_id']) > 0:
                domain_id = data['domain_id']
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            for i in domain_id:
                user_subscription = UserSubscription.objects.filter(domain=i).last()
                add_subscription = UserSubscription()
                add_subscription.domain_id = user_subscription.domain_id
                add_subscription.user_id = user_subscription.user_id
                add_subscription.opted_plan_id = user_subscription.previous_plan_id
                add_subscription.theme_id = user_subscription.theme_id
                add_subscription.start_date = user_subscription.start_date
                add_subscription.end_date = user_subscription.end_date
                add_subscription.is_free = False
                add_subscription.is_first_subscription = 1
                add_subscription.payment_amount = user_subscription.payment_amount
                add_subscription.previous_plan_id = user_subscription.previous_plan_id
                add_subscription.payment_status_id = user_subscription.payment_status_id
                add_subscription.subscription_status_id = user_subscription.subscription_status_id
                add_subscription.added_by_id = user_subscription.added_by_id
                add_subscription.updated_by_id = user_subscription.updated_by_id
                add_subscription.save()
            return Response(response.parsejson("Updated Successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddIdxPropertyApiView(APIView):
    """
    Add Idx Property
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "originating_system" in data and data['originating_system'] != "":
                originating_system = data['originating_system'].lower()
            else:
                return Response(response.parsejson("originating_system is required", "", status=403))

            if originating_system == 'mred':
                api_url = 'https://api-demo.mlsgrid.com/v2/Property'
                headers = {
                    'Authorization': 'Bearer 80f43f2a9800a28efb6cb182e8558508c77fa748',
                }
                params = {
                    '$filter': "OriginatingSystemName eq 'mred'",
                    # '$skip': 1,
                    '$top': 3,
                    '$expand': 'Media,Rooms,UnitTypes',
                }
                # Make the API request
                response_i = requests.get(api_url, headers=headers, params=params)
                response_data = ""
                if response_i.status_code == 200:
                    response_data = response_i.json()
                else:
                    response_data = ""
                mls_data = response_data['value']
                for mls_property in mls_data:
                    state = LookupState.objects.filter(iso_name=mls_property['MRD_LASTATE']).first()
                    property_type = LookupPropertyAsset.objects.filter(name = mls_property['PropertyType']).first()
                    listing_data = {
                        "title": "testing",
                        "description": mls_property['PublicRemarks'],
                        "domain": domain_id,
                        "agent": user_id,
                        "property_asset": property_type.id if property_type is not None else 3,  # Commercial/Residential/Land/Lots
                        "property_type": 4,
                        "sale_by_type": 1,
                        "beds": mls_property['BedroomsTotal'],
                        "baths": mls_property['BathroomsTotalInteger'],
                        "year_built": mls_property['YearBuilt'],
                        "square_footage": mls_property['LivingArea'],
                        "address_one": mls_property['MRD_LASTREETNAME'],
                        "city": mls_property['City'],
                        "postal_code": mls_property['PostalCode'],
                        "is_approved": True,
                        "state": state.id if state is not None else 1,
                        "country": state.country_id if state is not None else 1,
                        "status": 1,
                        "year_renovated": mls_property['YearBuilt'],
                        # "lot_size": 2800,
                        # "lot_size_unit": 2,
                        "lot_dimensions": mls_property['LotSizeDimensions'],
                        # "broker_co_op": True,
                        # "financing_available": True,
                        # "home_warranty": True,
                        "basement": True if len(mls_property['Basement']) else False,
                        "county": "",
                        "subdivision": "",
                        "school_district": "",
                        "property_taxes": int(mls_property["TaxAnnualAmount"]),
                        "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                        "hoa_fee": mls_property["AssociationFee"],
                        "garage_spaces": mls_property["GarageSpaces"],
                        "main_floor_area": mls_property['LivingArea'],
                        # "upper_floor_area": mls_property['LivingArea'],
                        # "basement_area": mls_property['LivingArea'],
                        "main_floor_bedroom": mls_property['BedroomsTotal'],
                        # "upper_floor_bedroom": mls_property['LivingArea'],
                        # "basement_bedroom": 2,
                        "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                        # "upper_floor_bathroom": 2,
                        # "basement_bathroom": 2,
                        "fireplace": mls_property["FireplacesTotal"],
                        # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                        "idx_property_id": mls_property["ListingId"]
                    }
                    auction = {
                        "domain": domain_id,
                        "property": 123,
                        "reserve_amount": mls_property['ListPrice'],
                        "bid_increments": 1000,
                        "status": 1,
                        "start_price": mls_property['ListPrice'],
                        "auction": 1,
                        "start_date": timezone.now() + timezone.timedelta(7),
                        "end_date": timezone.now() + timezone.timedelta(37)
                    }
                    with transaction.atomic():
                        serializer = AddDummyPropertySerializer(data=listing_data)
                        if serializer.is_valid():
                            property_data = serializer.save()
                            property_id = property_data.id
                            auction['property'] = property_id
                            serializer = AddDummyAuctionSerializer(data=auction)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                copy_errors = serializer.errors.copy()
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                return Response(response.parsejson(copy_errors, "", status=403))

                            media = mls_property['Media']
                            for img in media:
                                uploads = IdxPropertyUploads()
                                uploads.upload = img['MediaURL']
                                uploads.property_id = property_id
                                uploads.upload_type = 1
                                uploads.status_id = 1
                                uploads.save()

                        else:
                            copy_errors = serializer.errors.copy()
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(copy_errors, "", status=403))
            elif originating_system == 'idxbroker':
                api_url = 'https://api.idxbroker.com/clients/featured'
                headers = {
                    "Content-Type": 'application/json',
                    "accesskey": 'PYezsIXE3fsV6VthTq1Lox',
                    # "ancillarykey": 'PYezsIXE3fsV6VthTq1Lox',
                    # "apiversion": '1.8.0'
                }
                params = {
                    # 'linkName': 'Good_side_of_tracks',  # the link s url
                    'queryString': {
                        'idxID': 'a148',
                        # 'hp': 200000
                    }
                }
                # Make the API request
                response_i = requests.get(api_url, headers=headers)
                response_data = ""
                if response_i.status_code == 200:
                    response_data = response_i.json()
                else:
                    response_data = ""

                mls_data = response_data['data']
                for key, mls_property in mls_data.items():
                    state = LookupState.objects.filter(state_name=mls_property['state']).first()
                    if mls_property['idxPropType'] == "Lots and Land":
                        mls_property['idxPropType'] = "Land/Lots"
                    property_type = LookupPropertyAsset.objects.filter(name=mls_property['idxPropType']).first()
                    listing_data = {
                        "title": "testing",
                        "description": mls_property['remarksConcat'],
                        "domain": domain_id,
                        "agent": user_id,
                        "property_asset": property_type.id if property_type is not None else 3, # Commercial/Residential/Lands
                        "property_type": 4,
                        "sale_by_type": 1,
                        # "beds": mls_property['BedroomsTotal'],
                        "baths": mls_property['totalBaths'],
                        # "year_built": mls_property['YearBuilt'],
                        "total_acres": mls_property['acres'],
                        "address_one": mls_property['address'],
                        "city": mls_property['cityName'],
                        "postal_code": mls_property['zipcode'],
                        "is_approved": True,
                        "state": state.id if state is not None else 1,
                        "country": state.country_id if state is not None else 1,
                        "status": 1,
                        # "year_renovated": mls_property['YearBuilt'],
                        # "lot_size": 2800,
                        # "lot_size_unit": 2,
                        # "lot_dimensions": mls_property['LotSizeDimensions'],
                        # "broker_co_op": True,
                        # "financing_available": True,
                        # "home_warranty": True,
                        # "basement": True if len(mls_property['Basement']) else False,
                        "county": mls_property['countyName'],
                        "subdivision": "",
                        "school_district": "",
                        # "property_taxes": int(mls_property["TaxAnnualAmount"]),
                        # "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                        "hoa_fee": mls_property['advanced']["assocFeePrice"],
                        # "garage_spaces": mls_property["GarageSpaces"],
                        # "main_floor_area": mls_property['LivingArea'],
                        # "upper_floor_area": mls_property['LivingArea'],
                        # "basement_area": mls_property['LivingArea'],
                        # "main_floor_bedroom": mls_property['BedroomsTotal'],
                        # "upper_floor_bedroom": mls_property['LivingArea'],
                        # "basement_bedroom": 2,
                        # "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                        # "upper_floor_bathroom": 2,
                        # "basement_bathroom": 2,
                        # "fireplace": mls_property["FireplacesTotal"],
                        # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                        "idx_property_id": mls_property["listingID"],
                        "latitude": mls_property['latitude'],
                        "longitude": mls_property['longitude']
                    }

                    auction = {
                        "domain": domain_id,
                        "property": 123,
                        "reserve_amount": mls_property['price'],
                        "bid_increments": 1000,
                        "status": 1,
                        "start_price": mls_property['price'],
                        "auction": 1,
                        "start_date": timezone.now() + timezone.timedelta(7),
                        "end_date": timezone.now() + timezone.timedelta(37)
                    }
                    with transaction.atomic():
                        serializer = AddDummyPropertySerializer(data=listing_data)
                        if serializer.is_valid():
                            property_data = serializer.save()
                            property_id = property_data.id
                            auction['property'] = property_id
                            serializer = AddDummyAuctionSerializer(data=auction)
                            if serializer.is_valid():
                                serializer.save()
                            else:
                                copy_errors = serializer.errors.copy()
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                return Response(response.parsejson(copy_errors, "", status=403))

                            media = mls_property['image']
                            for keys, img in media.items():
                                if keys != 'totalCount':
                                    uploads = IdxPropertyUploads()
                                    uploads.upload = img['url']
                                    uploads.property_id = property_id
                                    uploads.upload_type = 1
                                    uploads.status_id = 1
                                    uploads.save()

                        else:
                            copy_errors = serializer.errors.copy()
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Property Successfully Created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class IdxPropertyCronApiView(APIView):
    """
    Idx Property Cron
    """
    # authentication_classes = [OAuth2Authentication, TokenAuthentication]
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        try:
            data = request.data
            user_id = 994
            domain_id = 356
            originating_system = 'idxbroker'

            api_url = 'https://api.idxbroker.com/clients/featured'
            headers = {
                "Content-Type": 'application/json',
                "accesskey": 'PYezsIXE3fsV6VthTq1Lox',
                # "ancillarykey": 'PYezsIXE3fsV6VthTq1Lox',
                # "apiversion": '1.8.0'
            }
            params = {
                # 'linkName': 'Good_side_of_tracks',  # the link s url
                'queryString': {
                    'idxID': 'a148',
                    # 'hp': 200000
                }
            }
            # Make the API request
            response_i = requests.get(api_url, headers=headers)
            response_data = ""
            if response_i.status_code == 200:
                response_data = response_i.json()
            else:
                response_data = ""

            mls_data = response_data['data']
            for key, mls_property in mls_data.items():
                idx_property_id = mls_property["listingID"]
                property_listing = PropertyListing.objects.filter(idx_property_id=idx_property_id).last()
                state = LookupState.objects.filter(state_name=mls_property['state']).first()
                if mls_property['idxPropType'] == "Lots and Land":
                    mls_property['idxPropType'] = "Land/Lots"
                property_type = LookupPropertyAsset.objects.filter(name=mls_property['idxPropType']).last()
                listing_data = {
                    "title": "testing",
                    "description": mls_property['remarksConcat'],
                    "domain": domain_id,
                    "agent": user_id,
                    "property_asset": property_type.id if property_type is not None else 3,
                    # Commercial/Residential/Lands
                    "property_type": 4,
                    "sale_by_type": 1,
                    # "beds": mls_property['BedroomsTotal'],
                    "baths": mls_property['totalBaths'],
                    # "year_built": mls_property['YearBuilt'],
                    "total_acres": mls_property['acres'],
                    "address_one": mls_property['address'],
                    "city": mls_property['cityName'],
                    "postal_code": mls_property['zipcode'],
                    "is_approved": True,
                    "state": state.id if state is not None else 1,
                    "country": state.country_id if state is not None else 1,
                    "status": 1,
                    # "year_renovated": mls_property['YearBuilt'],
                    # "lot_size": 2800,
                    # "lot_size_unit": 2,
                    # "lot_dimensions": mls_property['LotSizeDimensions'],
                    # "broker_co_op": True,
                    # "financing_available": True,
                    # "home_warranty": True,
                    # "basement": True if len(mls_property['Basement']) else False,
                    "county": mls_property['countyName'],
                    "subdivision": "",
                    "school_district": "",
                    # "property_taxes": int(mls_property["TaxAnnualAmount"]),
                    # "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                    "hoa_fee": mls_property['advanced']["assocFeePrice"],
                    # "garage_spaces": mls_property["GarageSpaces"],
                    # "main_floor_area": mls_property['LivingArea'],
                    # "upper_floor_area": mls_property['LivingArea'],
                    # "basement_area": mls_property['LivingArea'],
                    # "main_floor_bedroom": mls_property['BedroomsTotal'],
                    # "upper_floor_bedroom": mls_property['LivingArea'],
                    # "basement_bedroom": 2,
                    # "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                    # "upper_floor_bathroom": 2,
                    # "basement_bathroom": 2,
                    # "fireplace": mls_property["FireplacesTotal"],
                    # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                    "idx_property_id": mls_property["listingID"],
                    "latitude": mls_property['latitude'],
                    "longitude": mls_property['longitude']
                }

                auction = {
                    "domain": domain_id,
                    "property": 123,
                    "reserve_amount": mls_property['price'],
                    "bid_increments": 1000,
                    "status": 1,
                    "start_price": mls_property['price'],
                    "auction": 1,
                    "start_date": timezone.now() + timezone.timedelta(7),
                    "end_date": timezone.now() + timezone.timedelta(37)
                }
                with transaction.atomic():
                    serializer = AddDummyPropertySerializer(property_listing, data=listing_data)
                    if serializer.is_valid():
                        property_data = serializer.save()
                        property_id = property_data.id
                        auction['property'] = property_id
                        property_auction = PropertyAuction.objects.filter(property=property_id).last()
                        serializer = AddDummyAuctionSerializer(property_auction, data=auction)
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            copy_errors = serializer.errors.copy()
                            transaction.set_rollback(True)  # -----Rollback Transaction----
                            return Response(response.parsejson(copy_errors, "", status=403))

                        media = mls_property['image']
                        IdxPropertyUploads.objects.filter(property_id=property_id).delete()
                        for keys, img in media.items():
                            if keys != 'totalCount':
                                uploads = IdxPropertyUploads()
                                uploads.upload = img['url']
                                uploads.property_id = property_id
                                uploads.upload_type = 1
                                uploads.status_id = 1
                                uploads.save()

                    else:
                        copy_errors = serializer.errors.copy()
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Property Successfully Created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class IdxPropertyCronNewApiView(APIView):
    """
    Idx Property Cron
    """
    # authentication_classes = [OAuth2Authentication, TokenAuthentication]
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request):
        try:
            data = request.data
            user_id = 994
            domain_id = 356
            originating_system = 'idxbroker'
            network_mls_configuration = NetworkMlsConfiguration.objects.filter(status=1).order_by("-id")
            if network_mls_configuration is not None:
                for mls in network_mls_configuration:
                    # user_id = mls.domain.users_site_id.id
                    user_id = Users.objects.filter(site=mls.domain_id).last().id
                    domain_id = mls.domain_id
                    if mls.mls_type_id == 2:  # IDX Broker
                        api_url = 'https://api.idxbroker.com/clients/featured'
                        headers = {
                            "Content-Type": 'application/json',
                            "accesskey": mls.api_key,
                            # "ancillarykey": 'PYezsIXE3fsV6VthTq1Lox',
                            # "apiversion": '1.8.0'
                        }
                        params = {
                            # 'linkName': 'Good_side_of_tracks',  # the link s url
                            'queryString': {
                                'idxID': 'a148',
                                # 'hp': 200000
                            }
                        }
                        # Make the API request
                        response_i = requests.get(api_url, headers=headers)
                        response_data = ""
                        if response_i.status_code == 200:
                            response_data = response_i.json()
                        else:
                            response_data = {}

                        if 'data' in response_data:
                            mls_data = response_data['data']
                        else:
                            continue

                        for key, mls_property in mls_data.items():
                            idx_property_id = mls_property["listingID"]
                            property_listing = PropertyListing.objects.filter(idx_property_id=idx_property_id, domain_id=domain_id, status=1).last()
                            state = LookupState.objects.filter(state_name=mls_property['state']).first()
                            if mls_property['idxPropType'] == "Lots and Land":
                                mls_property['idxPropType'] = "Land/Lots"

                            property_type = LookupPropertyAsset.objects.filter(name=mls_property['idxPropType']).last()
                            if property_listing is None:
                                listing_data = {
                                    "title": "testing",
                                    "description": mls_property['remarksConcat'],
                                    "domain": domain_id,
                                    "agent": user_id,
                                    "property_asset": property_type.id if property_type is not None else 3,
                                    # Commercial/Residential/Lands
                                    "property_type": 4,
                                    "sale_by_type": 1,
                                    "beds": mls_property['bedrooms'] if 'bedrooms' in mls_property else None,
                                    "baths": mls_property['totalBaths'] if 'totalBaths' in mls_property else None,
                                    "year_built": mls_property['yearBuilt'] if 'yearBuilt' in mls_property else None,
                                    "square_footage": int(mls_property['sqFt'].replace(",", "")) if 'sqFt' in mls_property else None,
                                    "total_acres": mls_property['acres'],
                                    "address_one": mls_property['address'],
                                    "city": mls_property['cityName'],
                                    "postal_code": mls_property['zipcode'],
                                    "is_approved": True,
                                    "state": state.id if state is not None else 1,
                                    "country": state.country_id if state is not None else 1,
                                    "status": 1,
                                    # "year_renovated": mls_property['YearBuilt'],
                                    # "lot_size": 2800,
                                    # "lot_size_unit": 2,
                                    # "lot_dimensions": mls_property['LotSizeDimensions'],
                                    # "broker_co_op": True,
                                    # "financing_available": True,
                                    # "home_warranty": True,
                                    # "basement": True if len(mls_property['Basement']) else False,
                                    "county": mls_property['countyName'],
                                    "subdivision": "",
                                    "school_district": "",
                                    # "property_taxes": int(mls_property["TaxAnnualAmount"]),
                                    # "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                                    # "hoa_fee": mls_property['advanced']["assocFeePrice"],
                                    "hoa_fee": mls_property['advanced']["assocFeePrice"],
                                    # "garage_spaces": mls_property["GarageSpaces"],
                                    # "main_floor_area": mls_property['LivingArea'],
                                    # "upper_floor_area": mls_property['LivingArea'],
                                    # "basement_area": mls_property['LivingArea'],
                                    # "main_floor_bedroom": mls_property['BedroomsTotal'],
                                    # "upper_floor_bedroom": mls_property['LivingArea'],
                                    # "basement_bedroom": 2,
                                    # "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                                    # "upper_floor_bathroom": 2,
                                    # "basement_bathroom": 2,
                                    # "fireplace": mls_property["FireplacesTotal"],
                                    # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                                    "idx_property_id": mls_property["listingID"],
                                    "latitude": mls_property['latitude'],
                                    "longitude": mls_property['longitude']
                                }

                                auction = {
                                    "domain": domain_id,
                                    "property": 123,
                                    "reserve_amount": mls_property['price'],
                                    "bid_increments": 1000,
                                    "status": 1,
                                    "start_price": mls_property['price'],
                                    "auction": 1,
                                    "start_date": timezone.now() + timezone.timedelta(7),
                                    "end_date": timezone.now() + timezone.timedelta(37)
                                }
                            else:
                                listing_data = {
                                    "title": "testing",
                                    "description": mls_property['remarksConcat'],
                                    "property_type": property_listing.property_type_id,
                                    "domain": domain_id,
                                    "agent": user_id,
                                    "property_asset": property_type.id if property_type is not None else 3,
                                    # Commercial/Residential/Lands
                                    "beds": mls_property['bedrooms'] if 'bedrooms' in mls_property else None,
                                    "baths": mls_property['totalBaths'] if 'totalBaths' in mls_property else None,
                                    "year_built": mls_property['yearBuilt'] if 'yearBuilt' in mls_property else None,
                                    "square_footage": int(mls_property['sqFt'].replace(",", "")) if 'sqFt' in mls_property else None,
                                    "total_acres": mls_property['acres'],
                                    "address_one": mls_property['address'],
                                    "city": mls_property['cityName'],
                                    "postal_code": mls_property['zipcode'],
                                    "state": state.id if state is not None else 1,
                                    "country": state.country_id if state is not None else 1,
                                    "county": mls_property['countyName'],
                                    # "status": property_listing.status_id,
                                    "subdivision": "",
                                    "school_district": "",
                                    "hoa_fee": mls_property['advanced']["assocFeePrice"],
                                    "idx_property_id": mls_property["listingID"],
                                    "latitude": mls_property['latitude'],
                                    "longitude": mls_property['longitude']
                                }
                                auction = {
                                    "reserve_amount": mls_property['price'],
                                    "start_price": mls_property['price'],
                                }

                            with transaction.atomic():
                                serializer = AddDummyPropertySerializer(property_listing, data=listing_data)
                                if serializer.is_valid():
                                    property_data = serializer.save()
                                    property_id = property_data.id
                                    property_auction = PropertyAuction.objects.filter(property=property_id).last()
                                    auction['property'] = property_id
                                    auction['status'] = 1 if property_auction is None else property_auction.status_id
                                    serializer = AddDummyAuctionSerializer(property_auction, data=auction)
                                    if serializer.is_valid():
                                        serializer.save()
                                    else:
                                        copy_errors = serializer.errors.copy()
                                        transaction.set_rollback(True)  # -----Rollback Transaction----
                                        return Response(response.parsejson(copy_errors, "", status=403))

                                    media = mls_property['image']
                                    IdxPropertyUploads.objects.filter(property_id=property_id).delete()
                                    for keys, img in media.items():
                                        if keys != 'totalCount':
                                            uploads = IdxPropertyUploads()
                                            uploads.upload = img['url']
                                            uploads.property_id = property_id
                                            uploads.upload_type = 1
                                            uploads.status_id = 1
                                            uploads.save()

                                else:
                                    copy_errors = serializer.errors.copy()
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(copy_errors, "", status=403))
                    elif mls.mls_type_id == 3:  # MLS Grid
                        api_url = 'https://api-demo.mlsgrid.com/v2/Property'
                        headers = {
                            # 'Authorization': 'Bearer 80f43f2a9800a28efb6cb182e8558508c77fa748',
                            'Authorization': 'Bearer ' + mls.api_key,
                        }
                        params = {
                            # '$filter': "OriginatingSystemName eq 'mred'",
                            '$filter': "OriginatingSystemName eq '"+mls.originating_system.lower()+"'",
                            # '$skip': 1,
                            '$top': 3,
                            '$expand': 'Media,Rooms,UnitTypes',
                        }
                        # Make the API request
                        response_i = requests.get(api_url, headers=headers, params=params)
                        response_data = ""
                        if response_i.status_code == 200:
                            response_data = response_i.json()
                        else:
                            response_data = {}

                        if 'value' in response_data:
                            mls_data = response_data['value']
                        else:
                            continue

                        for mls_property in mls_data:
                            state = LookupState.objects.filter(iso_name=mls_property['MRD_LASTATE']).first()
                            property_type = LookupPropertyAsset.objects.filter(name=mls_property['PropertyType']).first()
                            property_listing = PropertyListing.objects.filter(idx_property_id=mls_property["ListingId"], domain_id=domain_id, status=1).last()
                            if property_listing is None:
                                listing_data = {
                                    "title": "testing",
                                    "description": mls_property['PublicRemarks'],
                                    "domain": domain_id,
                                    "agent": user_id,
                                    "property_asset": property_type.id if property_type is not None else 3,
                                    # Commercial/Residential/Land/Lots
                                    "property_type": 4,
                                    "sale_by_type": 1,
                                    "beds": mls_property['BedroomsTotal'],
                                    "baths": mls_property['BathroomsTotalInteger'],
                                    "year_built": mls_property['YearBuilt'],
                                    "square_footage": mls_property['LivingArea'],
                                    "address_one": mls_property['MRD_LASTREETNAME'],
                                    "city": mls_property['City'],
                                    "postal_code": mls_property['PostalCode'],
                                    "is_approved": True,
                                    "state": state.id if state is not None else 1,
                                    "country": state.country_id if state is not None else 1,
                                    "status": 1,
                                    "year_renovated": mls_property['YearBuilt'],
                                    # "lot_size": 2800,
                                    # "lot_size_unit": 2,
                                    "lot_dimensions": mls_property['LotSizeDimensions'],
                                    # "broker_co_op": True,
                                    # "financing_available": True,
                                    # "home_warranty": True,
                                    "basement": True if len(mls_property['Basement']) else False,
                                    "county": "",
                                    "subdivision": "",
                                    "school_district": "",
                                    "property_taxes": int(mls_property["TaxAnnualAmount"]),
                                    "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                                    "hoa_fee": mls_property["AssociationFee"],
                                    "garage_spaces": mls_property["GarageSpaces"],
                                    "main_floor_area": mls_property['LivingArea'],
                                    # "upper_floor_area": mls_property['LivingArea'],
                                    # "basement_area": mls_property['LivingArea'],
                                    "main_floor_bedroom": mls_property['BedroomsTotal'],
                                    # "upper_floor_bedroom": mls_property['LivingArea'],
                                    # "basement_bedroom": 2,
                                    "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                                    # "upper_floor_bathroom": 2,
                                    # "basement_bathroom": 2,
                                    "fireplace": mls_property["FireplacesTotal"],
                                    # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                                    "idx_property_id": mls_property["ListingId"]
                                }
                                auction = {
                                    "domain": domain_id,
                                    "property": 123,
                                    "reserve_amount": mls_property['ListPrice'],
                                    "bid_increments": 1000,
                                    "status": 1,
                                    "start_price": mls_property['ListPrice'],
                                    "auction": 1,
                                    "start_date": timezone.now() + timezone.timedelta(7),
                                    "end_date": timezone.now() + timezone.timedelta(37)
                                }
                            else:
                                listing_data = {
                                    "title": "testing",
                                    "description": mls_property['PublicRemarks'],
                                    "domain": domain_id,
                                    "agent": user_id,
                                    "property_asset": property_type.id if property_type is not None else 3,
                                    # Commercial/Residential/Land/Lots
                                    "property_type": property_listing.property_type_id,
                                    # "sale_by_type": 1,
                                    "beds": mls_property['BedroomsTotal'],
                                    "baths": mls_property['BathroomsTotalInteger'],
                                    "year_built": mls_property['YearBuilt'],
                                    "square_footage": mls_property['LivingArea'],
                                    "address_one": mls_property['MRD_LASTREETNAME'],
                                    "city": mls_property['City'],
                                    "postal_code": mls_property['PostalCode'],
                                    # "is_approved": True,
                                    "state": state.id if state is not None else 1,
                                    "country": state.country_id if state is not None else 1,
                                    # "status": property_listing.status_id,
                                    "year_renovated": mls_property['YearBuilt'],
                                    # "lot_size": 2800,
                                    # "lot_size_unit": 2,
                                    "lot_dimensions": mls_property['LotSizeDimensions'],
                                    # "broker_co_op": True,
                                    # "financing_available": True,
                                    # "home_warranty": True,
                                    "basement": True if len(mls_property['Basement']) else False,
                                    "county": "",
                                    "subdivision": "",
                                    "school_district": "",
                                    "property_taxes": int(mls_property["TaxAnnualAmount"]),
                                    "special_assessment_tax": int(mls_property["TaxAnnualAmount"]),
                                    "hoa_fee": mls_property["AssociationFee"],
                                    "garage_spaces": mls_property["GarageSpaces"],
                                    "main_floor_area": mls_property['LivingArea'],
                                    # "upper_floor_area": mls_property['LivingArea'],
                                    # "basement_area": mls_property['LivingArea'],
                                    "main_floor_bedroom": mls_property['BedroomsTotal'],
                                    # "upper_floor_bedroom": mls_property['LivingArea'],
                                    # "basement_bedroom": 2,
                                    "main_floor_bathroom": mls_property["BathroomsTotalInteger"],
                                    # "upper_floor_bathroom": 2,
                                    # "basement_bathroom": 2,
                                    "fireplace": mls_property["FireplacesTotal"],
                                    # "sale_terms": "The property is currently closed and is approved for conversion to Wyndham Hotels’ LaQuinta Inn brand. The site has an ideal location in the heart of Jacksonville and is minutes away from major attractions. The hotel is a seven-minute drive to the Jacksonville Mall with over 245,000 SF of retail space and Camp Lejeune. This hotel is also within proximity of the Onslow Memorial Hospital (162 beds), Brynn Marr Hospital (102 beds) and Naval Hospital Camp Lejeune (60 beds). Another attraction within 25 minutes of the property is the Hammocks Beach State Park, a North Carolina State Park situation on Bear Island, a three-mile long, undeveloped barrier island."
                                    "idx_property_id": mls_property["ListingId"]
                                }
                                auction = {
                                    "reserve_amount": mls_property['ListPrice'],
                                    "start_price": mls_property['ListPrice']
                                }

                            with transaction.atomic():
                                serializer = AddDummyPropertySerializer(property_listing, data=listing_data)
                                if serializer.is_valid():
                                    property_data = serializer.save()
                                    property_id = property_data.id
                                    property_auction = PropertyAuction.objects.filter(property=property_id).last()
                                    auction['property'] = property_id
                                    auction['status'] = 1 if property_auction is None else property_auction.status_id
                                    serializer = AddDummyAuctionSerializer(property_auction, data=auction)
                                    if serializer.is_valid():
                                        serializer.save()
                                    else:
                                        copy_errors = serializer.errors.copy()
                                        transaction.set_rollback(True)  # -----Rollback Transaction----
                                        return Response(response.parsejson(copy_errors, "", status=403))

                                    media = mls_property['Media']
                                    IdxPropertyUploads.objects.filter(property_id=property_id).delete()
                                    for img in media:
                                        uploads = IdxPropertyUploads()
                                        uploads.upload = img['MediaURL']
                                        uploads.property_id = property_id
                                        uploads.upload_type = 1
                                        uploads.status_id = 1
                                        uploads.save()

                                else:
                                    copy_errors = serializer.errors.copy()
                                    transaction.set_rollback(True)  # -----Rollback Transaction----
                                    return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Property Successfully Created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetPaymentSettingsApiView(APIView):
    """
    Get Payment Setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Domain not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                user = Users.objects.filter(id=user_id, site=domain_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            network_payment_credential = NetworkPaymentCredential.objects.filter(domain=domain_id, user=user_id, status=1).last()
            all_data = {}
            if network_payment_credential is not None:
                all_data['id'] = network_payment_credential.id
                all_data['stripe_public_key'] = network_payment_credential.stripe_public_key
                all_data['stripe_secret_key'] = network_payment_credential.stripe_secret_key
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SavePaymentSettingsApiView(APIView):
    """
    Save Payment Setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Domain not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = int(data['user'])
                user = Users.objects.filter(id=user, site=domain, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "stripe_public_key" in data and data['stripe_public_key'] != "":
                stripe_public_key = data['stripe_public_key']
            else:
                return Response(response.parsejson("stripe_public_key is required", "", status=403))

            if "stripe_secret_key" in data and data['stripe_secret_key'] != "":
                stripe_secret_key = data['stripe_secret_key']
            else:
                return Response(response.parsejson("stripe_secret_key is required", "", status=403))

            payment_id = None
            if "payment_id" in data and data['payment_id'] != "":
                payment_id = int(data['payment_id'])

            data['status'] = 1

            network_payment_credential = NetworkPaymentCredential.objects.filter(id=payment_id).last()
            if network_payment_credential is None:
                network_payment = NetworkPaymentCredential.objects.filter(domain=domain, user=user, status=1).last()
                if network_payment is not None:
                    return Response(response.parsejson("Data Already Exist.", "", status=403))

            serializer = NetworkPaymentCredentialSerializer(network_payment_credential, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))

            return Response(response.parsejson("Successfully Saved.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))           

