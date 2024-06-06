from django.db import models
from api.users.models import *


class Default(models.Model):
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "notifications"
        abstract = True


class NotificationTemplate(Default):
    site = models.ForeignKey(NetworkDomain, related_name="notification_template_site", on_delete=models.CASCADE,
                             null=True, blank=True)
    event = models.ForeignKey(LookupEvent, related_name="notification_template_event", on_delete=models.CASCADE)
    email_subject = models.CharField(max_length=255)
    email_content = models.TextField()
    notification_text = models.TextField(null=True, blank=True)
    push_notification_text = models.TextField(null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="notification_template_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="notification_template_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")
    status = models.ForeignKey(LookupStatus, related_name="notification_template_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "notification_template"


class EventNotification(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="event_notification_domain", on_delete=models.CASCADE, null=True, blank=True)
    notification_for = models.IntegerField(choices=((1, "Buyer"), (2, "Seller")), default=1)
    title = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    redirect_url = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=0)
    user = models.ForeignKey(Users, related_name="event_notification_user", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="event_notification_added_by", on_delete=models.CASCADE, db_column="added_by")
    status = models.ForeignKey(LookupStatus, related_name="event_notification_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "event_notification"

