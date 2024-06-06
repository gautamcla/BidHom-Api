# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from api.payments.models import *
from django.db import transaction
from api.payments.serializers import *
from django.utils import timezone
from api.packages.mail_service import send_email, compose_email, send_custom_email
from django.db.models import Q
from api.property.models import *
from api.bid.models import *


class PaymentSubscriptionDetailApiView(APIView):
    """
    Payment Subscription detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                # Translators: This message appears when domain_id is empty
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "plan_pricing_id" in data and data['plan_pricing_id'] != "":
                plan_pricing_id = int(data['plan_pricing_id'])
            else:
                # Translators: This message appears when subscription_id is empty
                return Response(response.parsejson("plan_pricing_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != domain_id:
                    return Response(response.parsejson("Not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            subscription_pricing = PlanPricing.objects.get(id=plan_pricing_id, cost__gt=0, is_active=1, subscription__is_active=1)
            serializer = PaymentSubscriptionDetailSerializer(subscription_pricing)
            all_data = {"subscription": serializer.data, "email": user.email}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CreateOrderApiView(APIView):
    """
    Create Order
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != domain_id:
                    return Response(response.parsejson("Not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
                plan_pricing = PlanPricing.objects.filter(id=plan_price_id, cost__gt=0, is_active=1, subscription__is_active=1).first()
                # plan_pricing = PlanPricing.objects.filter(subscription=plan_price_id, cost__gt=0, is_active=1, subscription__is_active=1).first()
                if plan_pricing is None:
                    return Response(response.parsejson("Plan not exist.", "", status=403))
            else:
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            if "amount" in data and data['amount'] != "":
                amount = data['amount']
            else:
                return Response(response.parsejson("amount is required", "", status=403))

            if "stripe_session" in data and data['stripe_session'] != "":
                stripe_session = data['stripe_session']
            else:
                return Response(response.parsejson("stripe_session is required", "", status=403))

            if "theme_id" in data and data['theme_id'] != "":
                theme_id = int(data['theme_id'])
            else:
                return Response(response.parsejson("theme_id is required", "", status=403))

            with transaction.atomic():
                # --------------------Check new and existing plan---------------
                # plan_subscribed = UserSubscription.objects.filter(domain=domain_id, subscription_status=1).last()
                # if plan_subscribed is not None and plan_subscribed.opted_plan.subscription_id == plan_price_id:
                #     return Response(response.parsejson("You have same plan.", "", status=403))
                try:
                    # ---------------Add data in to order table------------
                    order = Order()
                    order.domain_id = domain_id
                    order.user_id = user_id
                    order.payment_type_id = 1
                    order.amount = amount
                    order.stripe_session = stripe_session
                    order.save()
                    order_id = order.id
                    # ---------------Add data in to order detail table------------
                    order_detail = OrderDetail()
                    order_detail.order_id = order_id
                    order_detail.subscription_id = plan_pricing.subscription_id
                    order_detail.plan_price_id = plan_pricing.id
                    order_detail.theme_id = theme_id
                    order_detail.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

            return Response(response.parsejson("Order successfully created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CreatePaymentDetailApiView(APIView):
    """
    Create Payment Detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != domain_id:
                    return Response(response.parsejson("Not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
                plan_pricing = PlanPricing.objects.filter(id=plan_price_id, cost__gt=0, is_active=1, subscription__is_active=1).first()
                # plan_pricing = PlanPricing.objects.filter(subscription=plan_price_id, cost__gt=0, is_active=1, subscription__is_active=1).first()
                if plan_pricing is None:
                    return Response(response.parsejson("Plan not exist.", "", status=403))
            else:
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            if "theme_id" in data and data['theme_id'] != "":
                theme_id = int(data['theme_id'])
            else:
                return Response(response.parsejson("theme_id is required", "", status=403))

            with transaction.atomic():
                # --------------------Check new and existing plan---------------
                # plan_subscribed = UserSubscription.objects.filter(domain=domain_id, subscription_status=1).last()
                # if plan_subscribed is not None and plan_subscribed.opted_plan.subscription_id == plan_price_id:
                #     return Response(response.parsejson("You have same plan.", "", status=403))
                try:
                    PaymentDetail.objects.filter(domain_id=domain_id, user=user_id, status=1).update(status_id=2)
                    # ---------------Add data in to payment detail table------------
                    payment_detail = PaymentDetail()
                    payment_detail.amount = plan_pricing.cost
                    payment_detail.domain_id = domain_id
                    payment_detail.user_id = user_id
                    payment_detail.subscription_id = plan_pricing.subscription_id
                    payment_detail.plan_price_id = plan_pricing.id
                    payment_detail.theme_id = theme_id
                    payment_detail.status_id = 1
                    payment_detail.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

            return Response(response.parsejson("Order successfully created.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CreatePaymentDataApiView(APIView):
    """
    Create Payment Data
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                # Translators: This message appears when domain_id is empty
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).first()
                if user is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                elif user.site_id != domain_id:
                    return Response(response.parsejson("Not authorised user.", "", status=403))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            payment_detail = PaymentDetail.objects.filter(domain=domain_id, user=user_id, status=1).last()
            serializer = CreatePaymentDataSerializer(payment_detail)
            all_data = {"data": serializer.data}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class OrderSuccessApiView(APIView):
    """
    Order success
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "stripe_session" in data and data['stripe_session'] != "":
                stripe_session = data['stripe_session']
            else:
                return Response(response.parsejson("stripe_session is required", "", status=403))

            if "card_last_four" in data and data['card_last_four'] != "":
                card_last_four = data['card_last_four']
            else:
                return Response(response.parsejson("card_last_four is required", "", status=403))

            if "card_network" in data and data['card_network'] != "":
                card_network = data['card_network']
            else:
                return Response(response.parsejson("card_network is required", "", status=403))

            if "card_exp_month" in data and data['card_exp_month'] != "":
                card_exp_month = data['card_exp_month']
            else:
                return Response(response.parsejson("card_exp_month is required", "", status=403))

            if "card_exp_year" in data and data['card_exp_year'] != "":
                card_exp_year = data['card_exp_year']
            else:
                return Response(response.parsejson("card_exp_year is required", "", status=403))

            if "amount_paid" in data and data['amount_paid'] != "":
                amount_paid = data['amount_paid']
            else:
                return Response(response.parsejson("amount_paid is required", "", status=403))

            if "stripe_payment_intent" in data and data['stripe_payment_intent'] != "":
                stripe_payment_intent = data['stripe_payment_intent']
            else:
                return Response(response.parsejson("stripe_payment_intent is required", "", status=403))

            if "stripe_receipt_url" in data and data['stripe_receipt_url'] != "":
                stripe_receipt_url = data['stripe_receipt_url']
            else:
                return Response(response.parsejson("stripe_receipt_url is required", "", status=403))

            order = Order.objects.filter(stripe_session=stripe_session).first()
            if order is None:
                return Response(response.parsejson("Order not exist.", "", status=403))
            amount = order.amount
            order_id = order.id
            with transaction.atomic():
                try:
                    # ---------------Update data in to order table------------
                    order.card_last_four = card_last_four
                    order.card_network = card_network
                    order.card_exp_month = card_exp_month
                    order.card_exp_year = card_exp_year
                    order.amount_paid = amount_paid
                    order.stripe_payment_intent = stripe_payment_intent
                    order.stripe_receipt_url = stripe_receipt_url
                    order.partial_payment = 0 if amount == amount_paid else 1
                    order.payment_status = 1
                    order.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), "", status=403))

            if amount != amount_paid:
                return Response(response.parsejson("Partial payment.", "", status=403))
            order_detail = OrderDetail.objects.get(order=order_id)
            serializer = OrderSuccessSerializer(order_detail)
            return Response(response.parsejson("Payment successfully.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AfterPaymentChangePlanApiView(APIView):
    """
    After Payment Change Plan
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

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

            if "order_id" in data and data['order_id'] != "":
                transaction_id = int(data['order_id'])
            else:
                return Response(response.parsejson("order_id is required", "", status=403))

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
                plan_pricing = PlanPricing.objects.filter(id=opted_plan, is_active=1, plan_type__is_active=1, subscription__is_active=1).first()
                if plan_pricing is None:
                    return Response(response.parsejson("Plan not available.", "", status=403))
                amount = plan_pricing.cost
                new_opted_plan = plan_pricing.subscription_id
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

            data['start_date'] = timezone.now()
            data['end_date'] = timezone.now() + timezone.timedelta(days=plan_pricing.plan_type.duration_in_days)
            data['payment_amount'] = plan_pricing.cost
            data['payment_status'] = 1
            data['subscription_status'] = 1
            data['added_by'] = user_id
            data['updated_by'] = user_id

            # ----------------Match old plan with new plan------------
            plan_subscribed = UserSubscription.objects.filter(domain=site_id, subscription_status=1).last()
            if plan_subscribed is not None and plan_subscribed.opted_plan_id == opted_plan:
                return Response(response.parsejson("You have same plan.", "", status=403))

            subscription_id = None
            if plan_subscribed is not None:
                subscription_id = plan_subscribed.id

            with transaction.atomic():
                if int(new_opted_plan) == 2:
                    data['is_free'] = 1
                serializer = UserSubscriptionSerializer(data=data)
                if serializer.is_valid():
                    subscription = serializer.save()
                    new_subscription_id = subscription.id
                    order_id = new_subscription_id
                    # -------------Deactivating Old Plan-----------
                    if subscription_id is not None:
                        UserSubscription.objects.filter(id=subscription_id).update(subscription_status=2)

                    # ----------Subscription Payment-----------
                    subscription_payment_data = {}
                    subscription_payment_data['subscription'] = new_subscription_id
                    subscription_payment_data['payment'] = None
                    subscription_payment_data['order'] = transaction_id
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
                            user_theme_data['domain'] = site_id
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
                        if new_opted_plan == 2:
                            permission = LookupPermission.objects.filter(id__in=[5, 7], is_active=1).values("id")
                        elif new_opted_plan == 3:
                            permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).exclude(id=1).values("id")
                        elif new_opted_plan == 4:
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
            all_data = {}
            all_data['amount'] = amount
            all_data['order_id'] = "IC-" + str(order_id) if order_id is not None else ""
            all_data['transaction_id'] = "000" + str(transaction_id) if transaction_id is not None else ""
            # -------------Email -------------
            plan_detail = SubscriptionPlan.objects.get(id=new_opted_plan)
            current_plan = int(plan_pricing.cost)
            if current_plan > exit_plan:
                template_data = {"domain_id": site_id, "slug": "upgrade_plan"}
            else:
                template_data = {"domain_id": site_id, "slug": "plan_downgrade"}
            extra_data = {'web_url': settings.FRONT_BASE_URL, 'plan_name': plan_detail.plan_name,
                          'plan_price': plan_pricing.cost, 'plan_description': plan_detail.plan_desc,
                          "domain_id": site_id}
            compose_email(to_email=[users], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Plan updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuccessPaymentDetailApiView(APIView):
    """
    Success Payment Detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "payment_intent" in data and data['payment_intent'] != "":
                payment_intent = data['payment_intent']
            else:
                return Response(response.parsejson("payment_intent is required", "", status=403))
            subscription_payment = SubscriptionPayment.objects.filter(order__stripe_payment_intent=payment_intent).first()
            serializer = SuccessPaymentDetailSerializer(subscription_payment)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChangePlanSubscriptionApiView(APIView):
    """
    Change plan subscription
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
                user_id = data['user_id']
                users = Users.objects.filter(id=user_id, user_type=2, status=1).first()
                if users is None:
                    # Translators: This message appears when email not matched with user
                    return Response(response.parsejson("User Not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
            else:
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            payment_subscription = PaymentSubscription.objects.filter(domain=domain_id, user=user_id, status=1).last()
            if payment_subscription is not None and payment_subscription.opted_plan_id == plan_price_id:
                return Response(response.parsejson("Already requested for change plan.", "", status=403))
            else:
                payment_subscription = PaymentSubscription()
                payment_subscription.domain_id = domain_id
                payment_subscription.user_id = user_id
                payment_subscription.opted_plan_id = plan_price_id
                payment_subscription.status_id = 1
                payment_subscription.save()
            return Response(response.parsejson("Change Payment subscription accepted.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminTransactionListingApiView(APIView):
    """
    Admin Transaction Listing
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

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            domain = None
            if "domain" in data and len(data['domain']) > 0 and type(data['domain']) == list:
                domain = data['domain']

            order = Order.objects.filter(payment_status=1)
            if domain is not None:
                order = order.filter(domain__in=domain)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    order = order.filter(Q(domain__domain_name__icontains=search) | Q(payment_type__type_name__icontains=search) | Q(card_network__icontains=search) | Q(order_detail__subscription__plan_name__icontains=search) | Q(card_last_four__icontains=search) | Q(amount__icontains=search))
                else:
                    order = order.filter(Q(domain__domain_name__icontains=search) | Q(payment_type__type_name__icontains=search) | Q(card_network__icontains=search) | Q(order_detail__subscription__plan_name__icontains=search))
            total = order.count()
            portfolio = order.order_by("-id").only('id')[offset: limit]
            serializer = AdminTransactionListingSerializer(portfolio, many=True)
            all_data = {'total': total, 'data': serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckPaymentApiView(APIView):
    """
    Check Payment
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "stripe_price_id" in data and data['stripe_price_id'] != "":
                stripe_price_id = data['stripe_price_id']
            else:
                return Response(response.parsejson("stripe_price_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "amount" in data and data['amount'] != "":
                amount = data['amount']
            else:
                return Response(response.parsejson("amount is required", "", status=403))

            if "stripe_subscription_id" in data and data['stripe_subscription_id'] != "":
                stripe_subscription_id = data['stripe_subscription_id']
            else:
                return Response(response.parsejson("stripe_subscription_id is required", "", status=403))

            if "stripe_customer_id" in data and data['stripe_customer_id'] != "":
                stripe_customer_id = data['stripe_customer_id']
            else:
                return Response(response.parsejson("stripe_customer_id is required", "", status=403))

            payment_detail = PaymentDetail.objects.filter(user__email=email, status=1).last()
            if payment_detail is None:
                # return Response(response.parsejson("Payment not exist.", "", status=403))
                plan_pricing = PlanPricing.objects.filter(cost=amount, stripe_price_id=stripe_price_id, is_active=True, is_delete=False).first()
                user_theme = UserTheme.objects.filter(domain=domain_id, status=1).last()
                user_data = Users.objects.filter(email=email).first()
                payment_detail_create = PaymentDetail()
                payment_detail_create.amount = amount
                payment_detail_create.domain_id = domain_id
                payment_detail_create.user_id = user_data.id
                payment_detail_create.plan_price_id = plan_pricing.id
                payment_detail_create.theme_id = user_theme.theme_id
                payment_detail_create.status_id = 1
                payment_detail_create.save()
                payment_detail = PaymentDetail.objects.filter(domain=domain_id, user=user_data.id, status=1).last()

            # -----------------Inactive all payment for user----------------
            # PaymentDetail.objects.filter(user__email=email, status=1).update(status_id=2)
            # ---------------Insert Subscription id and Customer id-----------------
            Users.objects.filter(email=email).update(stripe_subscription_id=stripe_subscription_id, stripe_customer_id=stripe_customer_id)
            if payment_detail.plan_price.cost != amount:
                return Response(response.parsejson("Partial payment.", "", status=403))
            serializer = CheckPaymentSerializer(payment_detail)
            return Response(response.parsejson("Payment successfully.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PlanUpgradeAfterPaymentApiView(APIView):
    """
    Plan Upgrade After Payment
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

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
                plan_pricing = PlanPricing.objects.filter(id=opted_plan, is_active=1, plan_type__is_active=1, subscription__is_active=1).first()
                if plan_pricing is None:
                    return Response(response.parsejson("Plan not available.", "", status=403))
                amount = plan_pricing.cost
                new_opted_plan = plan_pricing.subscription_id
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

            data['start_date'] = timezone.now()
            data['end_date'] = timezone.now() + timezone.timedelta(days=plan_pricing.plan_type.duration_in_days)
            data['payment_amount'] = plan_pricing.cost
            data['payment_status'] = 1
            data['subscription_status'] = 1
            data['added_by'] = user_id
            data['updated_by'] = user_id

            # ----------------Match old plan with new plan------------
            plan_subscribed = UserSubscription.objects.filter(domain=site_id, subscription_status=1).last()
            # if plan_subscribed is not None and plan_subscribed.opted_plan_id == opted_plan:
            #     return Response(response.parsejson("You have same plan.", "", status=403))

            subscription_id = None
            if plan_subscribed is not None:
                subscription_id = plan_subscribed.id

            with transaction.atomic():
                if int(new_opted_plan) == 2:
                    data['is_free'] = 1
                serializer = UserSubscriptionSerializer(data=data)
                if serializer.is_valid():
                    subscription = serializer.save()
                    new_subscription_id = subscription.id
                    order_id = new_subscription_id
                    # -------------Deactivating Old Plan-----------
                    if subscription_id is not None:
                        UserSubscription.objects.filter(id=subscription_id).update(subscription_status=2)

                    # ----------Subscription Payment-----------
                    subscription_payment_data = {}
                    subscription_payment_data['subscription'] = new_subscription_id
                    subscription_payment_data['payment'] = None
                    subscription_payment_data['order'] = transaction_id
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
                            user_theme_data['domain'] = site_id
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
                        if new_opted_plan == 2:
                            permission = LookupPermission.objects.filter(id__in=[5, 7], is_active=1).values("id")
                        elif new_opted_plan == 3:
                            permission = LookupPermission.objects.filter(permission_type__in=[2, 3], is_active=1).exclude(id=1).values("id")
                        elif new_opted_plan == 4:
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
                        # -----------Update Payment Detail Table------------
                        payment_detail = PaymentDetail.objects.filter(domain=site_id, user_id=user_id, status=1).last()
                        payment_detail.status_id = 2
                        payment_detail.is_success = 1
                        payment_detail.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            all_data = {}
            all_data['amount'] = amount
            # all_data['order_id'] = "IC-" + str(order_id) if order_id is not None else ""
            # all_data['transaction_id'] = "000" + str(transaction_id) if transaction_id is not None else ""

            # -------------Email -------------
            plan_detail = SubscriptionPlan.objects.get(id=new_opted_plan)
            current_plan = int(plan_pricing.cost)
            if current_plan > exit_plan:
                template_data = {"domain_id": site_id, "slug": "upgrade_plan"}
            else:
                template_data = {"domain_id": site_id, "slug": "plan_downgrade"}
            extra_data = {'web_url': settings.FRONT_BASE_URL, 'plan_name': plan_detail.plan_name,
                          'plan_price': plan_pricing.cost, 'plan_description': plan_detail.plan_desc,
                          "domain_id": site_id}
            compose_email(to_email=[users], template_data=template_data, extra_data=extra_data)
            return Response(response.parsejson("Plan updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckPaymentSuccessApiView(APIView):
    """
    Check Payment Success
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            payment_detail = PaymentDetail.objects.filter(domain=domain_id, user=user_id).last()
            if payment_detail.status_id == 2 and payment_detail.is_success == 1:
                return Response(response.parsejson("Payment successfully.", {"cost": payment_detail.amount}, status=201))
            else:
                return Response(response.parsejson("Payment Pending", "", status=403))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckGlobalPaymentApiView(APIView):
    """
    Check Global Payment
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            # if "domain_id" in data and data['domain_id'] != "":
            #     domain_id = int(data['domain_id'])
            # else:
            #     return Response(response.parsejson("domain_id is required", "", status=403))

            if "stripe_price_id" in data and data['stripe_price_id'] != "":
                stripe_price_id = data['stripe_price_id']
            else:
                return Response(response.parsejson("stripe_price_id is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "amount" in data and data['amount'] != "":
                amount = data['amount']
            else:
                return Response(response.parsejson("amount is required", "", status=403))

            if "stripe_subscription_id" in data and data['stripe_subscription_id'] != "":
                stripe_subscription_id = data['stripe_subscription_id']
            else:
                return Response(response.parsejson("stripe_subscription_id is required", "", status=403))

            if "stripe_customer_id" in data and data['stripe_customer_id'] != "":
                stripe_customer_id = data['stripe_customer_id']
            else:
                return Response(response.parsejson("stripe_customer_id is required", "", status=403))

            payment_detail = PaymentDetail.objects.filter(user__email=email, status=1).last()
            if payment_detail is None:
                # plan_pricing = PlanPricing.objects.filter(cost=amount, stripe_price_id=stripe_price_id, is_active=True, is_delete=False).first()
                plan_pricing = PlanPricing.objects.filter(Q(cost=amount) & (Q(stripe_price_id=stripe_price_id) | Q(stripe_active_price_id=stripe_price_id)) & Q(is_active=True) & Q(is_delete=False)).first()
                user_data = Users.objects.filter(email=email).first()
                user_theme = UserTheme.objects.filter(domain=user_data.site_id, status=1).last()
                payment_detail_create = PaymentDetail()
                payment_detail_create.amount = amount
                payment_detail_create.domain_id = user_data.site_id
                payment_detail_create.user_id = user_data.id
                payment_detail_create.plan_price_id = plan_pricing.id
                payment_detail_create.theme_id = user_theme.theme_id
                payment_detail_create.status_id = 1
                payment_detail_create.save()
                payment_detail = PaymentDetail.objects.filter(domain=user_data.site_id, user=user_data.id, status=1).last()

            # -----------------Inactive all payment for user----------------
            # PaymentDetail.objects.filter(user__email=email, status=1).update(status_id=2)
            # ---------------Insert Subscription id and Customer id-----------------
            Users.objects.filter(email=email).update(stripe_subscription_id=stripe_subscription_id, stripe_customer_id=stripe_customer_id)
            if payment_detail.plan_price.cost != amount:
                return Response(response.parsejson("Partial payment.", "", status=403))
            serializer = CheckPaymentSerializer(payment_detail)
            return Response(response.parsejson("Payment successfully.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class StripePaymentDetailApiView(APIView):
    """
    Stripe Payment Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "plan_price_id" in data and data['plan_price_id'] != "":
                plan_price_id = int(data['plan_price_id'])
            else:
                # Translators: This message appears when plan_price_id is empty
                return Response(response.parsejson("plan_price_id is required", "", status=403))

            stripe_payment_detail = PlanPricing.objects.filter(id=plan_price_id, is_active=True).last()
            serializer = StripePaymentDetailSerializer(stripe_payment_detail)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class CheckPaymentSubscriptionApiView(APIView):
    """
    Check Payment Subscription
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = data['domain_id']
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            payment_detail = PaymentDetail.objects.filter(domain=domain_id, user=user_id).last()
            if payment_detail.status_id == 2 and payment_detail.is_success == 1:
                return Response(response.parsejson("Payment successfully.", {"cost": payment_detail.amount}, status=201))
            else:
                return Response(response.parsejson("Payment Pending", "", status=403))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
        

class PaymentListingDepositDetailApiView(APIView):
    """
    Payment Listing Deposit detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                # Translators: This message appears when domain_id is empty
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "listing_id" in data and data['listing_id'] != "":
                listing_id = int(data['listing_id'])
            else:
                # Translators: This message appears when listing_id is empty
                return Response(response.parsejson("listing_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1).first()
            else:
                return Response(response.parsejson("user is required", "", status=403))

            bid_registration = BidRegistration.objects.filter(property_id=listing_id, user_id=user_id, status_id=1).last()
            if bid_registration is not None:
                return Response(response.parsejson("Already requested to registration.", "", status=403))

            property_listing = PropertyListing.objects.get(id=listing_id, status=1)
            serializer = PaymentListingDepositDetailSerializer(property_listing)
            all_data = {"listing_deposit": serializer.data, "email": user.email, "first_name": user.first_name}
            payment_data = NetworkPaymentCredential.objects.filter(domain=domain_id, status=1).last()
            if payment_data is not None:
                all_data['stripe_public_key'] = payment_data.stripe_public_key
                all_data['stripe_secret_key'] = payment_data.stripe_secret_key
            else:
                all_data['stripe_public_key'] = ""
                all_data['stripe_secret_key'] = ""
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))     





