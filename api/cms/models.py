from django.db import models
from api.users.models import *


class Default(models.Model):
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "cms"
        abstract = True


class CmsContent(Default):
    site = models.ForeignKey(NetworkDomain, related_name="cms_content_site", on_delete=models.CASCADE, null=True, blank=True)
    page_title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, null=True, blank=True)
    meta_key_word = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.CharField(max_length=255, null=True, blank=True)
    meta_title = models.CharField(max_length=255)
    page_content = models.TextField()
    added_by = models.ForeignKey(Users, related_name="cms_content_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="cms_content_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")
    status = models.ForeignKey(LookupStatus, related_name="cms_content_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "cms_content"
        unique_together = ['site', 'slug']


class VideoTutorials(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="video_tutorials_domain", on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    video_url = models.CharField(max_length=255, null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="video_tutorials_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="video_tutorials_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")
    status = models.ForeignKey(LookupStatus, related_name="video_tutorials_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "video_tutorials"

