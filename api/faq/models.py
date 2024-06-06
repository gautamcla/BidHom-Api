from django.db import models
from api.users.models import *


class Default(models.Model):
    """This abstract class for common field

    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'faq'
        abstract = True


class Faq(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="faq_domain", on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField(null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    user_type = models.IntegerField(choices=((1, "Buyer"), (2, "Broker"), (3, "Agent")), default=1)
    status = models.ForeignKey(LookupStatus, related_name="faq_status", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="faq_added_by", on_delete=models.CASCADE)

    class Meta:
        db_table = "faq"
