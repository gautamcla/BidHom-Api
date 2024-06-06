# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from api.settings.models import *


class Default(models.Model):
    """This abstract class for common field

    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'users'
        abstract = True


class NetworkDomain(Default):
    domain_type = models.IntegerField(choices=((1, "main"), (2, "sub")), default=2)
    domain_name = models.CharField(max_length=255, unique=True)
    domain_url = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=1)
    is_delete = models.BooleanField(default=0)

    class Meta:
        db_table = "network_domain"


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
            Creates and saves a User with the given username, email, and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email),)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        users = self.create_user(email, password)
        users.is_admin = True
        users.is_staff = True
        users.save(using=self._db)
        return users


class Users(AbstractBaseUser):
    # REQUIRED_FIELDS = ['email']
    # USERNAME_FIELD = 'username'
    USERNAME_FIELD = 'email'

    site = models.ForeignKey(NetworkDomain, related_name="users_site_id", on_delete=models.CASCADE, null=True,
                             blank=True)
    user_type = models.ForeignKey(LookupUserType, related_name="users_user_type", on_delete=models.CASCADE, null=True)
    email = models.EmailField(max_length=254, unique=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    encrypted_password = models.CharField(max_length=255, null=True, blank=True)
    screen_name = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    avatar_image = models.CharField(max_length=255, null=True, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    activation_code = models.CharField(max_length=255, null=True, blank=True)
    verification_code = models.CharField(max_length=255, null=True, blank=True)
    activation_date = models.DateTimeField(null=True, blank=True)
    described_by = models.IntegerField(choices=((1, "Buyer"), (2, "Seller"), (3, "Broker/Agent")), default=1, null=True, blank=True)
    agree_term = models.BooleanField(default=1)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="users_country", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="users_status", on_delete=models.CASCADE, null=True, blank=True)
    update_on = models.DateTimeField(auto_now=True)
    added_on = models.DateTimeField(auto_now_add=True)
    # is_first_login = models.BooleanField(default=0)
    email_verified_on = models.DateTimeField(null=True, blank=True)
    website_tour = models.DateTimeField(null=True, blank=True)

    objects = MyUserManager()  # Set for admin users

    def has_perm(self, perm, obj=None):
        # return self.is_superuser
        return True

    def has_module_perms(self, app_label):
        # return self.is_superuser
        return True

    def is_staff(self):
        return True

    class Meta:
        db_table = 'users'


class CustomSiteSettings(Default):
    domain_id = models.ForeignKey(NetworkDomain, related_name="custom_site_settings", on_delete=models.CASCADE)
    settings_name = models.CharField(max_length=255)
    setting_value = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=1)
    added_by = models.ForeignKey(Users, related_name="custom_site_settings_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="custom_site_settings_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")

    class Meta:
        db_table = "custom_site_settings"
        unique_together = ['domain_id', 'settings_name']


class UserBusinessProfile(Default):
    user = models.ForeignKey(Users, related_name="user_business_profile", on_delete=models.CASCADE)
    company_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    mobile_no = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address_first = models.CharField(max_length=255, null=True, blank=True)
    address_second = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="user_business_profile_state", on_delete=models.CASCADE,
                              null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    licence_no = models.CharField(max_length=100, null=True, blank=True)
    company_logo = models.IntegerField(null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="user_business_profile_country", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="user_business_profile_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "user_business_profile"


class ProfileAddress(Default):
    user = models.ForeignKey(Users, related_name="profile_address_user", on_delete=models.CASCADE)
    address_type = models.ForeignKey(LookupAddressType, related_name="profile_address_address_type", on_delete=models.CASCADE)
    address_first = models.CharField(max_length=255, null=True, blank=True)
    address_second = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="profile_address_state", on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="profile_address_country", on_delete=models.CASCADE, null=True, blank=True)
    mobile_no = models.CharField(max_length=20, null=True, blank=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    county = models.ForeignKey(LookupStateCounty, related_name="profile_address_county", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="profile_address_status", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="profile_address_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="profile_address_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")

    class Meta:
        db_table = "profile_address"


class UserPasswordReset(Default):
    user = models.ForeignKey(Users, related_name="user_password_reset_user", on_delete=models.CASCADE)
    reset_token = models.CharField(max_length=255)
    reset_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=1)
    added_by = models.ForeignKey(Users, related_name="user_password_reset_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="user_password_reset_updated_by", on_delete=models.CASCADE,
                                   null=True, blank=True, db_column="updated_by")

    class Meta:
        db_table = "user_password_reset"


class UserUploads(Default):
    user = models.ForeignKey(Users, related_name="user_uploads_user", on_delete=models.CASCADE)
    site = models.ForeignKey(NetworkDomain, related_name="user_uploads_site", on_delete=models.CASCADE, null=True,
                             blank=True)
    file_size = models.CharField(max_length=51, null=True, blank=True)
    # doc_per_step = models.ForeignKey(DocumentsUploadPerStep, related_name="user_uploads_step", on_delete=models.CASCADE,
    #                                  null=True, blank=True)
    doc_file_name = models.CharField(max_length=255)
    # doc_type = models.ForeignKey(LookupDocType, related_name="user_uploads_doc_per_step", on_delete=models.CASCADE,
    #                              null=True, blank=True)
    document = models.ForeignKey(LookupDocuments, related_name="user_uploads_document", on_delete=models.CASCADE,
                                 null=True, blank=True)
    bucket_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=1)
    added_by = models.ForeignKey(Users, related_name="user_uploads_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="user_uploads_updated_by", on_delete=models.CASCADE, null=True,
                                   blank=True, db_column="updated_by")

    class Meta:
        db_table = "user_uploads"


class UserSubscription(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="user_subscription_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="user_subscription", on_delete=models.CASCADE)
    opted_plan = models.ForeignKey(PlanPricing, related_name="user_subscription_plan", on_delete=models.CASCADE)
    theme = models.ForeignKey(ThemesAvailable, related_name="user_subscription_theme", on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_free = models.BooleanField(default=0)
    is_first_subscription = models.IntegerField(default=0)
    payment_amount = models.FloatField(default=0.0)
    previous_plan = models.ForeignKey(PlanPricing, related_name="user_subscription_previous_plan", on_delete=models.CASCADE, null=True, blank=True)
    payment_status = models.ForeignKey(LookupStatus, related_name="user_subscription_payment", on_delete=models.CASCADE,
                                       db_column="payment_status")
    subscription_status = models.ForeignKey(LookupStatus, related_name="user_subscription_status",
                                            on_delete=models.CASCADE, db_column="subscription_status")
    added_by = models.ForeignKey(Users, related_name="user_subscription_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="user_subscription_updated_by", on_delete=models.CASCADE,
                                   null=True, blank=True, db_column="updated_by")

    class Meta:
        db_table = "user_subscription"


class UserTheme(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="user_theme_domain", on_delete=models.CASCADE)
    theme = models.ForeignKey(ThemesAvailable, related_name="user_theme_theme", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="user_theme_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "user_theme"


class NetworkUser(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_user_domain", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="network_user", on_delete=models.CASCADE)
    is_agent = models.BooleanField(default=0)
    status = models.ForeignKey(LookupStatus, related_name="network_user_status", on_delete=models.CASCADE, null=True, blank=True)
    agent_added_on = models.DateTimeField(null=True, blank=True)
    is_upgrade = models.BooleanField(default=0)
    brokerage_name = models.CharField(max_length=255, null=True, blank=True)
    licence_number = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "network_user"
        unique_together = ['domain', 'user']


class NetworkArticleCategory(Default):
    name = models.CharField(max_length=255)
    status = models.ForeignKey(LookupStatus, related_name="network_article_category_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "network_article_category"


class NetworkArticles(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_articles_domain", on_delete=models.CASCADE, null=True, blank=True)
    asset = models.ForeignKey(NetworkArticleCategory, related_name="network_articles_asset", on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    author_image = models.ForeignKey(UserUploads, related_name="network_articles_author_image", on_delete=models.CASCADE,
                                     null=True, blank=True)
    upload = models.ForeignKey(UserUploads, related_name="network_articles_upload", on_delete=models.CASCADE,
                               null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_articles_status", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="network_articles_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="network_articles_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")
    publish_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "network_articles"


class NetworkUpload(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_upload_domain", on_delete=models.CASCADE)
    upload = models.ForeignKey(UserUploads, related_name="network_upload_upload", on_delete=models.CASCADE, null=True,
                               blank=True)
    upload_type = models.IntegerField(choices=((1, "Banner"), (2, "Footer company"), (3, "About image")), null=True,
                                      blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_upload_status", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="network_upload_added_by", on_delete=models.CASCADE,
                                 db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="network_upload_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by")

    class Meta:
        db_table = "network_upload"


class NetworkAuction(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_auction_domain", on_delete=models.CASCADE)
    auction_name = models.CharField(max_length=255, null=True, blank=True)
    upload = models.ForeignKey(UserUploads, related_name="network_auction_upload", on_delete=models.CASCADE, null=True,
                               blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_auction_status", on_delete=models.CASCADE, null=True,
                               blank=True)
    added_by = models.ForeignKey(Users, related_name="network_auction_added_by", on_delete=models.CASCADE,
                                 db_column="added_by", null=True, blank=True)
    updated_by = models.ForeignKey(Users, related_name="network_auction_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by", null=True, blank=True)

    class Meta:
        db_table = "network_auction"


class ExpertiseIcon(models.Model):
    icon_name = models.CharField(max_length=100)
    icon_type = models.IntegerField(choices=((1, "Residential"), (2, "Land"), (3, "Commercial"), (4, "Auction")))
    status = models.ForeignKey(LookupStatus, related_name="expertise_icon_status", on_delete=models.CASCADE, blank=True)

    class Meta:
        db_table = "expertise_icon"


class NetworkExpertise(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_expertise_domain", on_delete=models.CASCADE)
    expertise_name = models.CharField(max_length=255, null=True, blank=True)
    upload = models.ForeignKey(UserUploads, related_name="network_expertise_upload", on_delete=models.CASCADE,
                               null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_expertise_status", on_delete=models.CASCADE,
                               null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="network_expertise_added_by", on_delete=models.CASCADE,
                                 db_column="added_by", null=True, blank=True)
    updated_by = models.ForeignKey(Users, related_name="network_expertise_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by", null=True, blank=True)
    expertise_icon = models.ForeignKey(ExpertiseIcon, related_name="network_expertise_expertise_icon",
                                       on_delete=models.CASCADE, null=True, blank=True)
    expertise_icon_type = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "network_expertise"


class NetworkSocialAccount(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_social_account_domain", on_delete=models.CASCADE)
    account_type = models.IntegerField(choices=((1, "facebook"), (2, "twitter"), (3, "youtube"), (4, "linkedin"), (5, "instagram")), null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    position = models.IntegerField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_social_account_status", on_delete=models.CASCADE,
                               null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="network_social_account_added_by", on_delete=models.CASCADE,
                                 db_column="added_by", null=True, blank=True)
    updated_by = models.ForeignKey(Users, related_name="network_social_account_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by", null=True, blank=True)

    class Meta:
        db_table = "network_social_account"


class DashboardNumbers(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="dashboard_numbers_domain", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    status = models.ForeignKey(LookupStatus, related_name="dashboard_numbers_status", on_delete=models.CASCADE,
                               null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="dashboard_numbers_added_by", on_delete=models.CASCADE,
                                 db_column="added_by", null=True, blank=True)
    updated_by = models.ForeignKey(Users, related_name="dashboard_numbers_updated_by", on_delete=models.CASCADE,
                                   db_column="updated_by", null=True, blank=True)

    class Meta:
        db_table = "dashboard_numbers"


class UserPermission(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="user_permission_domain", on_delete=models.CASCADE, null=True,
                               blank=True)
    user = models.ForeignKey(Users, related_name="user_permission_user", on_delete=models.CASCADE, null=True, blank=True)
    permission = models.ForeignKey(LookupPermission, related_name="user_permission_permission", on_delete=models.CASCADE)
    is_permission = models.BooleanField(default=1)

    class Meta:
        db_table = "user_permission"


class ContactUs(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="contact_us_domain", on_delete=models.CASCADE, null=True,
                               blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    user_type = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="contact_us_status", on_delete=models.CASCADE, blank=True)

    class Meta:
        db_table = "contact_us"


class NetworkTestimonials(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="network_testimonials_domain", on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    author_name = models.CharField(max_length=255, null=True, blank=True)
    author_image = models.ForeignKey(UserUploads, related_name="network_testimonials_author_image", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_testimonials_status", on_delete=models.CASCADE)
    added_by = models.ForeignKey(Users, related_name="network_testimonials_added_by", on_delete=models.CASCADE, db_column="added_by")
    updated_by = models.ForeignKey(Users, related_name="network_testimonials_updated_by", on_delete=models.CASCADE, db_column="updated_by")

    class Meta:
        db_table = "network_testimonials"


class TempRegistration(Default):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.IntegerField(default=1)
    is_business_email_send = models.IntegerField(default=0)

    class Meta:
        db_table = "temp_registration"


class MlsType(Default):
    name = models.CharField(max_length=255, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="mls_type_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "mls_type"


class NetworkMlsConfiguration(Default):
    api_key = models.CharField(max_length=255, null=True, blank=True)
    originating_system = models.CharField(max_length=255, null=True, blank=True)
    domain = models.ForeignKey(NetworkDomain, related_name="network_mls_configuration", on_delete=models.CASCADE)
    mls_type = models.ForeignKey(MlsType, related_name="mls_type_network_mls_configuration", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_mls_configuration_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "network_mls_configuration"


class NetworkPaymentCredential(Default):
    stripe_public_key = models.CharField(max_length=255, null=True, blank=True)
    stripe_secret_key = models.CharField(max_length=255, null=True, blank=True)
    domain = models.ForeignKey(NetworkDomain, related_name="network_payment_credential_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="network_payment_credential_user", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="network_payment_credential_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "network_payment_credential"        