# -*- coding: utf-8 -*-
from django.db import models
from api.property.models import *


class Default(models.Model):
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "advertisement"
        abstract = True


class Advertisement(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="advertisement_domain", on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    image = models.ForeignKey(UserUploads, related_name="advertisement_image", on_delete=models.CASCADE, null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="advertisement_added_by", on_delete=models.CASCADE, db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="advertisement_updated_by", on_delete=models.CASCADE, db_column="updated_by")
    status = models.ForeignKey(LookupStatus, related_name="advertisement_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "advertisement"


class TrackAdvertisement(Default):
    advertisement = models.ForeignKey(Advertisement, related_name="track_advertisement", on_delete=models.CASCADE, null=True, blank=True)
    domain = models.ForeignKey(NetworkDomain, related_name="track_advertisement_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="track_advertisement_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="track_advertisement_user", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "track_advertisement"

