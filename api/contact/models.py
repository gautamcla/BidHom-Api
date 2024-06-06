from django.db import models
from api.property.models import *


class Default(models.Model):
    """This abstract class for common field

    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'contact'
        abstract = True


class MasterChat(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="master_chat_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="master_chat_property", on_delete=models.CASCADE, null=True, blank=True)
    buyer = models.ForeignKey(Users, related_name="master_chat_sender", on_delete=models.CASCADE)
    seller = models.ForeignKey(Users, related_name="master_chat_receiver", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="master_chat_added_by", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="master_chat_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "master_chat"


class Chat(Default):
    master = models.ForeignKey(MasterChat, related_name="chat_master", on_delete=models.CASCADE)
    message = models.TextField()
    sender = models.ForeignKey(Users, related_name="chat_sender", on_delete=models.CASCADE, null=True, blank=True)
    receiver = models.ForeignKey(Users, related_name="chat_receiver", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="chat_status", on_delete=models.CASCADE)
    is_read = models.BooleanField(default=0)

    class Meta:
        db_table = "chat"


class ChatDocuments(Default):
    chat = models.ForeignKey(Chat, related_name="chat_documents_chat", on_delete=models.CASCADE)
    document = models.ForeignKey(UserUploads, related_name="chat_documents_user_uploads", on_delete=models.CASCADE)

    class Meta:
        db_table = "chat_documents"
