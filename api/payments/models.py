from django.db import models
from api.users.models import *


class Default(models.Model):
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'payments'
        abstract = True


class PaymentType(Default):
    type_name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "payment_type"


class UserPayment(Default):
    user = models.ForeignKey(Users, related_name="user_payment", on_delete=models.CASCADE)
    payment_type = models.ForeignKey(PaymentType, related_name="user_payment_type", on_delete=models.CASCADE,
                                     db_column="payment_type")
    cc_ac_no = models.CharField(max_length=16)
    cc_ac_type_name = models.CharField(max_length=20)
    payment_mode = models.CharField(max_length=20)
    payment_amount = models.FloatField(default=0.0)
    amount_paid = models.FloatField(default=0.0)
    response_code = models.CharField(max_length=5)
    response_message = models.CharField(max_length=255)
    transaction_type = models.IntegerField(choices=((1, "one time"), (2, "recurring")))
    subscription_status = models.ForeignKey(LookupStatus, related_name="user_payment_status", on_delete=models.CASCADE,
                                            db_column="status")

    class Meta:
        db_table = "user_payment"


class Order(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="order_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="order_user", on_delete=models.CASCADE)
    payment_type = models.ForeignKey(PaymentType, related_name="order_payment_type", on_delete=models.CASCADE, db_column="payment_type")
    card_last_four = models.IntegerField(null=True, blank=True)
    card_network = models.CharField(max_length=60, null=True, blank=True)
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    amount = models.FloatField(default=0.0)
    amount_paid = models.FloatField(default=0.0)
    stripe_payment_intent = models.TextField(null=True, blank=True)
    stripe_session = models.TextField(null=True, blank=True)
    stripe_receipt_url = models.TextField(null=True, blank=True)
    partial_payment = models.BooleanField(default=0)
    payment_status = models.BooleanField(default=0)

    class Meta:
        db_table = "order"


class OrderDetail(Default):
    order = models.ForeignKey(Order, related_name="order_detail", on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(SubscriptionPlan, related_name="order_detail_subscription", on_delete=models.CASCADE)
    plan_price = models.ForeignKey(PlanPricing, related_name="order_detail_plan_price", on_delete=models.CASCADE)
    theme = models.ForeignKey(ThemesAvailable, related_name="order_detail_theme", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "order_detail"


class PaymentDetail(Default):
    amount = models.FloatField(default=0.0)
    domain = models.ForeignKey(NetworkDomain, related_name="payment_detail_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="payment_detail_user", on_delete=models.CASCADE)
    subscription = models.ForeignKey(SubscriptionPlan, related_name="payment_detail_subscription", on_delete=models.CASCADE)
    plan_price = models.ForeignKey(PlanPricing, related_name="payment_detail_plan_price", on_delete=models.CASCADE)
    theme = models.ForeignKey(ThemesAvailable, related_name="payment_detail_theme", on_delete=models.CASCADE, null=True, blank=True)
    is_success = models.IntegerField(default=0)
    status = models.ForeignKey(LookupStatus, related_name="payment_detail_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "payment_detail"


class SubscriptionPayment(Default):
    subscription = models.ForeignKey(UserSubscription, related_name="subscription_payment", on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey(UserPayment, related_name="user_subscription_payment", on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, related_name="subscription_payment_order", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "subscription_payment"
        unique_together = ('subscription', 'payment')


class PaymentSubscription(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="payment_subscription_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="payment_subscription_user", on_delete=models.CASCADE)
    opted_plan = models.ForeignKey(PlanPricing, related_name="payment_subscription_opted_plan", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="payment_subscription_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "payment_subscription"
