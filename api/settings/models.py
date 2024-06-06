# -*- coding: utf-8 -*-
from django.db import models


class Default(models.Model):
    """This abstract class for common field

    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'settings'
        abstract = True


class SiteSetting(Default):
    settings_name = models.CharField(max_length=255, unique=True)
    slug = models.CharField(max_length=255, unique=True, null=True, blank=True)
    setting_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=1)

    class Meta:
        db_table = "site_setting"


class LookupStatus(models.Model):
    status_name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_status"


class LookupObject(models.Model):
    object_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_object"


class LookupObjectStatus(models.Model):
    object = models.ForeignKey(LookupObject, related_name="lookup_object_status_object", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="lookup_object_status", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_object_status"


class LookupCountry(models.Model):
    iso_name = models.CharField(max_length=3, unique=True)
    alpha2_code = models.CharField(max_length=2, unique=True, null=True, blank=True)
    country_name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_country"


class LookupState(models.Model):
    country = models.ForeignKey(LookupCountry, related_name="lookup_state_country", on_delete=models.CASCADE)
    iso_name = models.CharField(max_length=3)
    state_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('country', 'iso_name', 'state_name')
        db_table = "lookup_state"


class LookupZip(models.Model):
    zip = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state_iso = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    timezone = models.CharField(max_length=255, null=True, blank=True)
    saving_time = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="lookup_zip_state", on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_zip"


class ThemesAvailable(models.Model):
    theme_name = models.CharField(max_length=255, unique=True)
    theme_dir = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "themes_available"


class LookupStateCounty(models.Model):
    state = models.ForeignKey(LookupState, related_name="lookup_state_county_state", on_delete=models.CASCADE)
    county_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_state_county"


class LookupUserType(models.Model):
    user_type = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_user_type"


class LookupPropertyAsset(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_property_asset"


class LookupPropertyType(models.Model):
    property_type = models.CharField(max_length=50, unique=True)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_property_type_asset", on_delete=models.CASCADE,
                              null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_property_type"


class LookupAuctionType(models.Model):
    auction_type = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_auction_type"


class LookupDocuments(models.Model):
    document_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_documents"


class LookupAddressType(models.Model):
    address_type = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_address_type"


class LookupUploadStep(models.Model):
    uploads_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_upload_step"


class DocumentsUploadPerStep(models.Model):
    step = models.ForeignKey(LookupUploadStep, related_name="documents_upload_per_step", on_delete=models.CASCADE)
    user_type = models.ForeignKey(LookupUserType, related_name="documents_upload_per_step_user_type", on_delete=models.CASCADE)
    document = models.ForeignKey(LookupDocuments, related_name="documents_upload_per_step_document", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "documents_upload_per_step"


class LookupDocType(models.Model):
    doc_type_name = models.CharField(max_length=6, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_doc_type"


class PlanType(models.Model):
    type_name = models.CharField(max_length=50, unique=True)
    duration_in_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_type"


class SubscriptionPlan(Default):
    plan_name = models.CharField(max_length=100, unique=True)
    plan_desc = models.TextField()
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "subscription_plan"


class PlanBenefits(models.Model):
    plan = models.ForeignKey(PlanType, related_name="plan_benefits_plan", on_delete=models.CASCADE)
    benefits = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "plan_benefits"


class PlanPricing(models.Model):
    subscription = models.ForeignKey(SubscriptionPlan, related_name="plan_pricing_subscription", on_delete=models.CASCADE)
    plan_type = models.ForeignKey(PlanType, related_name="plan_pricing_plan_type", on_delete=models.CASCADE)
    cost = models.FloatField(default=0.0)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_button_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_payment_link = models.TextField(null=True, blank=True)
    stripe_active_price_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_active_button_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_active_payment_link = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_pricing"


class LookupEvent(models.Model):
    event_name = models.CharField(max_length=50, unique=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_event"


class LookupPermission(Default):
    name = models.CharField(max_length=255)
    permission_type = models.IntegerField(choices=((1, "Super Admin"), (2, "Subdomain"), (3, "Both")))
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_permission"

# ---------------Property lookup---------------


class LookupPropertySubType(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_property_subtype", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_property_subtype"
        unique_together = ('name', 'asset')


class LookupTermsAccepted(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_terms_accepted", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_terms_accepted"
        unique_together = ('name', 'asset')


class LookupOccupiedBy(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_occupied_by", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_occupied_by"
        unique_together = ('name', 'asset')


class LookupOwnership(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_ownership", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_ownership"
        unique_together = ('name', 'asset')


class LookupPossession(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_possession", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_possession"
        unique_together = ('name', 'asset')


class LookupLotSize(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_lot_size", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_lot_size"
        unique_together = ('name', 'asset')


class LookupStyle(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_style", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_style"
        unique_together = ('name', 'asset')


class LookupCooling(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_cooling", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_cooling"
        unique_together = ('name', 'asset')


class LookupStories(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_stories", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_stories"
        unique_together = ('name', 'asset')


class LookupHeating(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_heating", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_heating"
        unique_together = ('name', 'asset')


class LookupElectric(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_electric", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_electric"
        unique_together = ('name', 'asset')


class LookupGas(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_gas", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_gas"
        unique_together = ('name', 'asset')


class LookupRecentUpdates(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_recent_updates", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_recent_updates"
        unique_together = ('name', 'asset')


class LookupWater(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_water", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_water"
        unique_together = ('name', 'asset')


class LookupSecurityFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_security_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_security_features"
        unique_together = ('name', 'asset')


class LookupSewer(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_sewer", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_sewer"
        unique_together = ('name', 'asset')


class LookupTaxExemptions(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_tax_exemptions", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_tax_exemptions"
        unique_together = ('name', 'asset')


class LookupZoning(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_zoning", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_zoning"
        unique_together = ('name', 'asset')


class LookupAmenities(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_amenities", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_amenities"
        unique_together = ('name', 'asset')


class LookupKitchenFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_kitchen_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_kitchen_features"
        unique_together = ('name', 'asset')


class LookupAppliances(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_appliances", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_appliances"
        unique_together = ('name', 'asset')


class LookupFlooring(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_flooring", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_flooring"
        unique_together = ('name', 'asset')


class LookupWindows(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_windows", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_windows"
        unique_together = ('name', 'asset')


class LookupBedroomFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_bedroom_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_bedroom_features"
        unique_together = ('name', 'asset')


class LookupBathroomFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_bathroom_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_bathroom_features"
        unique_together = ('name', 'asset')


class LookupOtherRooms(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_other_rooms", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_other_rooms"
        unique_together = ('name', 'asset')


class LookupOtherFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_other_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_other_features"
        unique_together = ('name', 'asset')


class LookupMasterBedroomFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_master_bedroom_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_master_bedroom_features"
        unique_together = ('name', 'asset')


class LookupFireplaceType(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_fireplace_type", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_fireplace_type"
        unique_together = ('name', 'asset')


class LookupBasementFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_basement_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_basement_features"
        unique_together = ('name', 'asset')


class LookupHandicapAmenities(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_handicap_amenities", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_handicap_amenities"
        unique_together = ('name', 'asset')


class LookupConstruction(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_construction", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_construction"
        unique_together = ('name', 'asset')


class LookupExteriorFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_exterior_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_exterior_features"
        unique_together = ('name', 'asset')


class LookupGarageParking(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_garage_parking", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_garage_parking"
        unique_together = ('name', 'asset')


class LookupGarageFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_garage_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_garage_features"
        unique_together = ('name', 'asset')


class LookupRoof(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_roof", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_roof"
        unique_together = ('name', 'asset')


class LookupOutbuildings(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_outbuildings", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_outbuildings"
        unique_together = ('name', 'asset')


class LookupFoundation(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_foundation", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_foundation"
        unique_together = ('name', 'asset')


class LookupLocationFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_location_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_location_features"
        unique_together = ('name', 'asset')


class LookupFence(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_fence", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_fence"
        unique_together = ('name', 'asset')


class LookupRoadFrontage(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_road_frontage", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_road_frontage"
        unique_together = ('name', 'asset')


class LookupPool(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_pool", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_pool"
        unique_together = ('name', 'asset')


class LookupPropertyFaces(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_property_faces", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_property_faces"
        unique_together = ('name', 'asset')


class LookupLeaseType(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_lease_type", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_lease_type"
        unique_together = ('name', 'asset')


class LookupTenantPays(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_tenant_pays", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_tenant_pays"
        unique_together = ('name', 'asset')


class LookupInclusions(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_inclusions", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_inclusions"
        unique_together = ('name', 'asset')


class LookupBuildingClass(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_building_class", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_building_class"
        unique_together = ('name', 'asset')


class LookupInteriorFeatures(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_interior_features", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_interior_features"
        unique_together = ('name', 'asset')


class LookupMineralRights(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_mineral_rights", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_mineral_rights"
        unique_together = ('name', 'asset')


class LookupEasements(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_easements", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_easements"
        unique_together = ('name', 'asset')


class LookupSurvey(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_survey", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_survey"
        unique_together = ('name', 'asset')


class LookupUtilities(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_utilities", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_utilities"
        unique_together = ('name', 'asset')


class LookupImprovements(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_improvements", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_improvements"
        unique_together = ('name', 'asset')


class LookupTopography(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_topography", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_topography"
        unique_together = ('name', 'asset')


class LookupWildlife(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_wildlife", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_wildlife"
        unique_together = ('name', 'asset')


class LookupFish(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_fish", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_fish"
        unique_together = ('name', 'asset')


class LookupIrrigationSystem(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_irrigation_system", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_irrigation_system"
        unique_together = ('name', 'asset')


class LookupRecreation(models.Model):
    name = models.CharField(max_length=100)
    asset = models.ForeignKey(LookupPropertyAsset, related_name="lookup_recreation", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_recreation"
        unique_together = ('name', 'asset')


class LookupTimezone(models.Model):
    timezone = models.CharField(max_length=100)
    offset = models.CharField(max_length=100)
    offset_dst = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "lookup_timezone"




