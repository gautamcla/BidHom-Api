# -*- coding: utf-8 -*-
from django.db import models
from api.users.models import *


class Default(models.Model):
    """This abstract class for common field
    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'property'
        abstract = True


class PropertyListing(Default):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    property_price = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)
    domain = models.ForeignKey(NetworkDomain, related_name="property_listing_domain", on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, related_name="property_listing_agent", on_delete=models.CASCADE)
    property_asset = models.ForeignKey(LookupPropertyAsset, related_name="property_listing_property_asset", on_delete=models.CASCADE)
    property_type = models.ForeignKey(LookupPropertyType, related_name="property_listing_property_type", on_delete=models.CASCADE)
    broker_co_op = models.BooleanField(default=0, null=True, blank=True)
    financing_available = models.BooleanField(default=0, null=True, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    baths = models.IntegerField(null=True, blank=True)
    year_built = models.IntegerField(null=True, blank=True)
    year_renovated = models.IntegerField(null=True, blank=True)
    square_footage = models.IntegerField(null=True, blank=True)
    lot_size = models.IntegerField(null=True, blank=True)
    lot_size_unit = models.ForeignKey(LookupLotSize, related_name="property_listing_lot_size_unit", on_delete=models.CASCADE, null=True, blank=True)
    home_warranty = models.BooleanField(default=1, null=True, blank=True)
    lot_dimensions = models.CharField(max_length=100, null=True, blank=True)
    garage_spaces = models.IntegerField(null=True, blank=True)
    basement = models.BooleanField(default=1, null=True, blank=True)
    property_taxes = models.IntegerField(null=True, blank=True)
    special_assessment_tax = models.IntegerField(null=True, blank=True)
    hoa_fee = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    hoa_fee_type = models.IntegerField(choices=((1, "Monthly"), (2, "Annual")), default=1, null=True, blank=True)
    subdivision = models.CharField(max_length=255, null=True, blank=True)
    school_district = models.CharField(max_length=255, null=True, blank=True)
    upper_floor_area = models.FloatField(default=0.0, null=True, blank=True)
    main_floor_area = models.FloatField(default=0.0, null=True, blank=True)
    basement_area = models.FloatField(default=0.0, null=True, blank=True)
    upper_floor_bedroom = models.IntegerField(null=True, blank=True)
    main_floor_bedroom = models.IntegerField(null=True, blank=True)
    basement_bedroom = models.IntegerField(null=True, blank=True)
    upper_floor_bathroom = models.IntegerField(null=True, blank=True)
    main_floor_bathroom = models.IntegerField(null=True, blank=True)
    basement_bathroom = models.IntegerField(null=True, blank=True)
    fireplace = models.IntegerField(null=True, blank=True)
    lease_expiration = models.DateTimeField(null=True, blank=True)
    total_buildings = models.IntegerField(null=True, blank=True)
    total_units = models.IntegerField(null=True, blank=True)
    net_operating_income = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    occupancy = models.DecimalField(default=0.00, max_digits=6, decimal_places=2, null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)
    cap_rate = models.DecimalField(default=0.00, max_digits=6, decimal_places=2, null=True, blank=True)
    average_monthly_rate = models.DecimalField(default=0.00, max_digits=16, decimal_places=2, null=True, blank=True)
    total_rooms = models.IntegerField(null=True, blank=True)
    total_bedrooms = models.IntegerField(null=True, blank=True)
    total_bathrooms = models.IntegerField(null=True, blank=True)
    total_public_restrooms = models.IntegerField(null=True, blank=True)
    ceiling_height = models.IntegerField(null=True, blank=True)
    total_acres = models.FloatField(default=0.00, null=True, blank=True)
    dryland_acres = models.FloatField(default=0.00, null=True, blank=True)
    irrigated_acres = models.FloatField(default=0.00, null=True, blank=True)
    grass_acres = models.FloatField(default=0.00, null=True, blank=True)
    pasture_fenced_acres = models.FloatField(default=0.00, null=True, blank=True)
    crp_acres = models.FloatField(default=0.00, null=True, blank=True)
    timber_acres = models.FloatField(default=0.00, null=True, blank=True)
    lot_acres = models.FloatField(default=0.00, null=True, blank=True)
    balance_other_acres = models.FloatField(default=0.00, null=True, blank=True)
    fsa_information = models.TextField(null=True, blank=True)
    crop_yield_history = models.TextField(null=True, blank=True)
    ponds = models.IntegerField(null=True, blank=True)
    wells = models.IntegerField(null=True, blank=True)
    soil_productivity_rating = models.TextField(null=True, blank=True)
    county = models.CharField(max_length=100, null=True, blank=True)
    livestock_carrying_capacity = models.IntegerField(null=True, blank=True)
    annual_payment = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    contract_expire = models.DateTimeField(null=True, blank=True)
    property_lat = models.CharField(max_length=100, null=True, blank=True)
    property_lon = models.CharField(max_length=100, null=True, blank=True)
    address_one = models.TextField(null=True, blank=True)
    address_two = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="property_listing_state", on_delete=models.CASCADE, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    is_map_view = models.BooleanField(default=1)
    is_street_view = models.BooleanField(default=1)
    is_arial_view = models.BooleanField(default=1)
    create_step = models.IntegerField(choices=((1, "First"), (2, "Second"), (3, "Third"), (4, "Fourth")), default=1)
    sale_by_type = models.ForeignKey(LookupAuctionType, related_name="property_listing_sale_by_type", on_delete=models.CASCADE, null=True, blank=True)
    buyer = models.ForeignKey(Users, related_name='property_listing_buyer', null=True, blank=True, on_delete=models.CASCADE)
    sold_price = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)
    date_sold = models.DateTimeField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_listing_status", on_delete=models.CASCADE, null=True, blank=True)
    closing_status = models.ForeignKey(LookupStatus, related_name="property_listing_closing_status", on_delete=models.CASCADE, null=True, blank=True)
    added_by = models.ForeignKey(Users, related_name="property_listing_added_by", on_delete=models.CASCADE, db_column="added_by", null=True, blank=True)
    updated_by = models.ForeignKey(Users, related_name="property_listing_updated_by", on_delete=models.CASCADE, null=True, blank=True, db_column="updated_by")
    sale_terms = models.TextField(null=True, blank=True)
    is_featured = models.BooleanField(default=0, null=True, blank=True)
    is_approved = models.BooleanField(default=0, null=True, blank=True)
    map_url = models.TextField(null=True, blank=True)
    ordering = models.IntegerField(null=True, blank=True)
    winner = models.ForeignKey(Users, related_name="property_listing_winner", on_delete=models.CASCADE, null=True, blank=True)
    read_by_auction_dashboard = models.BooleanField(default=1)
    auction_location = models.TextField(null=True, blank=True)
    due_diligence_period = models.IntegerField(null=True, blank=True)
    escrow_period = models.IntegerField(null=True, blank=True)
    earnest_deposit = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    earnest_deposit_type = models.IntegerField(choices=((1, "Amount"), (2, "Percentage")), default=1)
    highest_best_format = models.IntegerField(choices=((1, "Traditional"), (2, "Private"), (3, "Public")), default=3)
    latitude = models.CharField(max_length=251, null=True, blank=True)
    longitude = models.CharField(max_length=251, null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="property_listing_country", on_delete=models.CASCADE, null=True, blank=True)
    idx_property_id = models.CharField(max_length=251, null=True, blank=True)
    buyers_premium = models.BooleanField(default=0)
    buyers_premium_percentage = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    buyers_premium_min_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    is_deposit_required = models.BooleanField(default=0, null=True, blank=True)
    deposit_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)

    class Meta:
        db_table = "property_listing"


class PropertyUploads(Default):
    upload = models.ForeignKey(UserUploads, related_name="property_uploads", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="property_uploads_property", on_delete=models.CASCADE)
    upload_type = models.IntegerField(choices=((1, "Images"), (2, "Video"), (3, "Documents")))
    status = models.ForeignKey(LookupStatus, related_name="property_uploads_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_uploads"


class PropertySubtype(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_subtype", on_delete=models.CASCADE)
    subtype = models.ForeignKey(LookupPropertySubType, related_name="subtype", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_subtype"
class PropertyTermAccepted(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_term_accepted", on_delete=models.CASCADE)
    term_accepted = models.ForeignKey(LookupTermsAccepted, related_name="term_accepted", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_term_accepted"
class PropertyOccupiedBy(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_occupied_by", on_delete=models.CASCADE)
    occupied_by = models.ForeignKey(LookupOccupiedBy, related_name="occupied_by", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_occupied_by"
class PropertyOwnership(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_ownership", on_delete=models.CASCADE)
    ownership = models.ForeignKey(LookupOwnership, related_name="occupied_by", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_ownership"
class PropertyPossession(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_possession", on_delete=models.CASCADE)
    possession = models.ForeignKey(LookupPossession, related_name="possession", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_possession"
class PropertyStyle(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_style", on_delete=models.CASCADE)
    style = models.ForeignKey(LookupStyle, related_name="style", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_style"
class PropertyCooling(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_cooling", on_delete=models.CASCADE)
    cooling = models.ForeignKey(LookupCooling, related_name="cooling", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_cooling"
class PropertyStories(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_stories", on_delete=models.CASCADE)
    stories = models.ForeignKey(LookupStories, related_name="stories", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_stories"
class PropertyHeating(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_heating", on_delete=models.CASCADE)
    heating = models.ForeignKey(LookupHeating, related_name="heating", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_heating"
class PropertyElectric(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_electric", on_delete=models.CASCADE)
    electric = models.ForeignKey(LookupElectric, related_name="electric", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_electric"
class PropertyGas(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_gas", on_delete=models.CASCADE)
    gas = models.ForeignKey(LookupGas, related_name="gas", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_gas"
class PropertyRecentUpdates(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_recent_updates", on_delete=models.CASCADE)
    recent_updates = models.ForeignKey(LookupRecentUpdates, related_name="recent_updates", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_recent_updates"
class PropertyWater(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_water", on_delete=models.CASCADE)
    water = models.ForeignKey(LookupWater, related_name="water", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_water"
class PropertySecurityFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_security_features", on_delete=models.CASCADE)
    security_features = models.ForeignKey(LookupSecurityFeatures, related_name="security_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_security_features"
class PropertySewer(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_sewer", on_delete=models.CASCADE)
    sewer = models.ForeignKey(LookupSewer, related_name="sewer", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_sewer"
class PropertyTaxExemptions(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_tax_exemptions", on_delete=models.CASCADE)
    tax_exemptions = models.ForeignKey(LookupTaxExemptions, related_name="tax_exemptions", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_tax_exemptions"
class PropertyZoning(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_zoning", on_delete=models.CASCADE)
    zoning = models.ForeignKey(LookupZoning, related_name="zoning", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_zoning"
class PropertyAmenities(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_amenities", on_delete=models.CASCADE)
    amenities = models.ForeignKey(LookupAmenities, related_name="amenities", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_amenities"
class PropertyKitchenFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_kitchen_features", on_delete=models.CASCADE)
    kitchen_features = models.ForeignKey(LookupKitchenFeatures, related_name="kitchen_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_kitchen_features"
class PropertyAppliances(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_appliances", on_delete=models.CASCADE)
    appliances = models.ForeignKey(LookupAppliances, related_name="appliances", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_appliances"
class PropertyFlooring(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_flooring", on_delete=models.CASCADE)
    flooring = models.ForeignKey(LookupFlooring, related_name="flooring", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_flooring"
class PropertyWindows(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_windows", on_delete=models.CASCADE)
    windows = models.ForeignKey(LookupWindows, related_name="windows", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_windows"
class PropertyBedroomFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_bedroom_features", on_delete=models.CASCADE)
    bedroom_features = models.ForeignKey(LookupBedroomFeatures, related_name="bedroom_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_bedroom_features"
class PropertyOtherRooms(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_other_rooms", on_delete=models.CASCADE)
    other_rooms = models.ForeignKey(LookupOtherRooms, related_name="other_rooms", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_other_rooms"
class PropertyBathroomFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_bathroom_features", on_delete=models.CASCADE)
    bathroom_features = models.ForeignKey(LookupBathroomFeatures, related_name="bathroom_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_bathroom_features"
class PropertyOtherFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_other_features", on_delete=models.CASCADE)
    other_features = models.ForeignKey(LookupOtherFeatures, related_name="other_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_other_features"
class PropertyMasterBedroomFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_master_bedroom_features", on_delete=models.CASCADE)
    master_bedroom_features = models.ForeignKey(LookupMasterBedroomFeatures, related_name="master_bedroom_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_master_bedroom_features"
class PropertyFireplaceType(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_fireplace_type", on_delete=models.CASCADE)
    fireplace_type = models.ForeignKey(LookupFireplaceType, related_name="fireplace_type", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_fireplace_type"
class PropertyBasementFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_basement_features", on_delete=models.CASCADE)
    basement_features = models.ForeignKey(LookupBasementFeatures, related_name="basement_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_basement_features"
class PropertyHandicapAmenities(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_handicap_amenities", on_delete=models.CASCADE)
    handicap_amenities = models.ForeignKey(LookupHandicapAmenities, related_name="handicap_amenities", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_handicap_amenities"
class PropertyConstruction(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_construction", on_delete=models.CASCADE)
    construction = models.ForeignKey(LookupConstruction, related_name="construction", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_construction"
class PropertyGarageParking(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_garage_parking", on_delete=models.CASCADE)
    garage_parking = models.ForeignKey(LookupGarageParking, related_name="garage_parking", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_garage_parking"
class PropertyExteriorFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_exterior_features", on_delete=models.CASCADE)
    exterior_features = models.ForeignKey(LookupExteriorFeatures, related_name="exterior_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_exterior_features"
class PropertyGarageFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_garage_features", on_delete=models.CASCADE)
    garage_features = models.ForeignKey(LookupGarageFeatures, related_name="garage_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_garage_features"
class PropertyRoof(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_roof", on_delete=models.CASCADE)
    roof = models.ForeignKey(LookupRoof, related_name="roof", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_roof"
class PropertyOutbuildings(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_outbuildings", on_delete=models.CASCADE)
    outbuildings = models.ForeignKey(LookupOutbuildings, related_name="outbuildings", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_outbuildings"
class PropertyFoundation(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_foundation", on_delete=models.CASCADE)
    foundation = models.ForeignKey(LookupFoundation, related_name="foundation", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_foundation"
class PropertyLocationFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_location_features", on_delete=models.CASCADE)
    location_features = models.ForeignKey(LookupLocationFeatures, related_name="location_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_location_features"
class PropertyFence(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_fence", on_delete=models.CASCADE)
    fence = models.ForeignKey(LookupFence, related_name="fence", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_fence"
class PropertyRoadFrontage(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_road_frontage", on_delete=models.CASCADE)
    road_frontage = models.ForeignKey(LookupRoadFrontage, related_name="road_frontage", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_road_frontage"
class PropertyPool(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_pool", on_delete=models.CASCADE)
    pool = models.ForeignKey(LookupPool, related_name="pool", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_pool"
class PropertyPropertyFaces(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_property_faces", on_delete=models.CASCADE)
    property_faces = models.ForeignKey(LookupPropertyFaces, related_name="property_faces", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_property_faces"
class PropertyLeaseType(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_lease_type", on_delete=models.CASCADE)
    lease_type = models.ForeignKey(LookupLeaseType, related_name="lease_type", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_lease_type"
class PropertyTenantPays(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_tenant_pays", on_delete=models.CASCADE)
    tenant_pays = models.ForeignKey(LookupTenantPays, related_name="tenant_pays", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_tenant_pays"
class PropertyInclusions(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_inclusions", on_delete=models.CASCADE)
    inclusions = models.ForeignKey(LookupInclusions, related_name="inclusions", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_inclusions"
class PropertyBuildingClass(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_building_class", on_delete=models.CASCADE)
    building_class = models.ForeignKey(LookupBuildingClass, related_name="building_class", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_building_class"
class PropertyInteriorFeatures(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_interior_features", on_delete=models.CASCADE)
    interior_features = models.ForeignKey(LookupInteriorFeatures, related_name="interior_features", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_interior_features"
class PropertyMineralRights(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_mineral_rights", on_delete=models.CASCADE)
    mineral_rights = models.ForeignKey(LookupInteriorFeatures, related_name="mineral_rights", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_mineral_rights"
class PropertyEasements(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_easements", on_delete=models.CASCADE)
    easements = models.ForeignKey(LookupInteriorFeatures, related_name="easements", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_easements"
class PropertySurvey(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_survey", on_delete=models.CASCADE)
    survey = models.ForeignKey(LookupInteriorFeatures, related_name="survey", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_survey"
class PropertyUtilities(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_utilities", on_delete=models.CASCADE)
    utilities = models.ForeignKey(LookupInteriorFeatures, related_name="utilities", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_utilities"
class PropertyImprovements(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_improvements", on_delete=models.CASCADE)
    improvements = models.ForeignKey(LookupInteriorFeatures, related_name="improvements", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_improvements"
class PropertyTopography(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_topography", on_delete=models.CASCADE)
    topography = models.ForeignKey(LookupInteriorFeatures, related_name="topography", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_topography"
class PropertyWildlife(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_wildlife", on_delete=models.CASCADE)
    wildlife = models.ForeignKey(LookupInteriorFeatures, related_name="wildlife", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_wildlife"
class PropertyFish(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_fish", on_delete=models.CASCADE)
    fish = models.ForeignKey(LookupInteriorFeatures, related_name="fish", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_fish"
class PropertyIrrigationSystem(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_irrigation_system", on_delete=models.CASCADE)
    irrigation_system = models.ForeignKey(LookupInteriorFeatures, related_name="irrigation_system", on_delete=models.CASCADE)
    class Meta:
        db_table = "property_irrigation_system"


class PropertyRecreation(Default):
    property = models.ForeignKey(PropertyListing, related_name="property_recreation", on_delete=models.CASCADE)
    recreation = models.ForeignKey(LookupInteriorFeatures, related_name="recreation", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_recreation"


class PropertyAuction(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_auction_domain", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="property_auction", on_delete=models.CASCADE)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    # bid_increments = models.IntegerField(null=True, blank=True)
    # reserve_amount = models.IntegerField(null=True, blank=True)
    reserve_amount = models.FloatField(null=True, blank=True)
    bid_increments = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    # reserve_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_auction_status", on_delete=models.CASCADE)
    time_zone = models.ForeignKey(LookupTimezone, related_name="property_auction_timezone", on_delete=models.CASCADE, null=True, blank=True)
    start_price = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    open_house_start_date = models.DateTimeField(null=True, blank=True)
    open_house_end_date = models.DateTimeField(null=True, blank=True)
    offer_amount = models.FloatField(default=0.0, null=True, blank=True)
    auction = models.ForeignKey(LookupAuctionType, related_name="auction_property_auction", on_delete=models.CASCADE, null=True, blank=True)
    original_end_date = models.DateTimeField(null=True, blank=True)
    ending_soon_threshold = models.IntegerField(null=True, blank=True)  # Local setting for auction
    bid_extension_time_period = models.IntegerField(null=True, blank=True)  # Local setting for auction
    # bid_extension_amount = models.IntegerField(null=True, blank=True)  # Local setting for auction
    bid_extension_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2, null=True, blank=True)
    un_priced = models.BooleanField(default=0)
    insider_price_decrease = models.FloatField(default=0.0, null=True, blank=True)
    insider_decreased_price = models.FloatField(default=0.0, null=True, blank=True)
    dutch_time = models.IntegerField(null=True, blank=True)
    dutch_end_time = models.DateTimeField(null=True, blank=True)
    dutch_pause_time = models.IntegerField(null=True, blank=True)
    sealed_time = models.IntegerField(null=True, blank=True)
    sealed_start_time = models.DateTimeField(null=True, blank=True)
    sealed_end_time = models.DateTimeField(null=True, blank=True)
    sealed_pause_time = models.IntegerField(null=True, blank=True)
    english_time = models.IntegerField(null=True, blank=True)
    english_start_time = models.DateTimeField(null=True, blank=True)
    english_end_time = models.DateTimeField(null=True, blank=True)
    required_all = models.BooleanField(default=0)

    class Meta:
        db_table = "property_auction"


class PropertyView(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_view_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="property_view_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="property_view_user", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_view"


class PropertySettings(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_settings_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="property_settings_property", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="property_settings_user", on_delete=models.CASCADE)
    is_broker = models.BooleanField(default=0)
    is_agent = models.BooleanField(default=0)
    auto_approval = models.BooleanField(default=1)
    bid_limit = models.BigIntegerField(null=True, blank=True)
    show_reverse_not_met = models.BooleanField(default=1)
    is_log_time_extension = models.BooleanField(default=1)
    time_flash = models.BigIntegerField(null=True, blank=True)
    log_time_extension = models.BigIntegerField(null=True, blank=True)
    remain_time_to_add_extension = models.BigIntegerField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_settings_status", on_delete=models.CASCADE)
    is_deposit_required = models.BooleanField(default=0, null=True, blank=True)
    deposit_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)

    class Meta:
        db_table = "property_settings"
        unique_together = ['domain', 'property']


class FavouriteProperty(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="favourite_property_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="property_favourite_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="favourite_property_user", on_delete=models.CASCADE)

    class Meta:
        db_table = "favourite_property"
        unique_together = ['domain', 'property', 'user']


class WatchProperty(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="watch_property_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="watch_property_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="watch_property_user", on_delete=models.CASCADE)

    class Meta:
        db_table = "watch_property"
        unique_together = ['domain', 'property', 'user']


class ScheduleTour(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="schedule_tour_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="schedule_tour_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="schedule_tour_user", on_delete=models.CASCADE)
    schedule_date = models.DateTimeField()
    tour_type = models.IntegerField(choices=((1, "In Person"), (2, "Video Chat")), default=1)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    availability = models.IntegerField(choices=((1, "Morning"), (2, "Afternoon"), (3, "Evening"), (4, "Flexible")), default=1)
    status = models.ForeignKey(LookupStatus, related_name="schedule_tour_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "schedule_tour"


class DocumentVaultVisit(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="document_vault_visit_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="document_vault_visit_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="document_vault_visit_user", on_delete=models.CASCADE)
    documents = models.ForeignKey(PropertyUploads, related_name="document_vault_visit_documents", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="document_vault_visit_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "document_vault_visit"


class PropertyEvaluatorCategory(Default):
    name = models.CharField(max_length=251)
    status = models.ForeignKey(LookupStatus, related_name="property_evaluator_category_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_evaluator_category"


class PropertyEvaluatorQuestion(Default):
    category = models.ForeignKey(PropertyEvaluatorCategory, related_name="property_evaluator_question_category", on_delete=models.CASCADE)
    question = models.TextField(null=True, blank=True)
    placeholder = models.TextField(null=True, blank=True)
    option_type = models.IntegerField(choices=((1, "TextArea"), (2, "Radio"), (3, "DropDown"), (4, "Image"), (5, "Rating"), (6, "Map")), default=1)
    property_type = models.ForeignKey(LookupPropertyAsset, related_name="property_evaluator_question_property_type", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_evaluator_question_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_evaluator_question"


class PropertyEvaluatorQuestionOption(Default):
    question = models.ForeignKey(PropertyEvaluatorQuestion, related_name="property_evaluator_question_option", on_delete=models.CASCADE)
    option = models.CharField(max_length=251)
    status = models.ForeignKey(LookupStatus, related_name="property_evaluator_question_option_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_evaluator_question_option"


class PropertyEvaluatorDomain(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_evaluator_domain", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="property_evaluator_domain_user", on_delete=models.CASCADE)
    assign_to = models.ForeignKey(Users, related_name="property_evaluator_domain_assign_to", on_delete=models.CASCADE, null=True, blank=True)
    complete_status = models.ForeignKey(LookupStatus, related_name="property_evaluator_domain_complete_status", on_delete=models.CASCADE, default=16)
    review_msg = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_evaluator_domain_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_evaluator_domain"


class PropertyEvaluatorUserAnswer(Default):
    property_evaluator = models.ForeignKey(PropertyEvaluatorDomain, related_name="property_evaluator_user_answer_property_evaluator", on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey(PropertyEvaluatorQuestion, related_name="property_evaluator_user_answer", on_delete=models.CASCADE)
    answer = models.CharField(max_length=251, null=True, blank=True)

    class Meta:
        db_table = "property_evaluator_user_answer"


class PropertyEvaluatorDocAnswer(Default):
    answer = models.ForeignKey(PropertyEvaluatorUserAnswer, related_name="property_evaluator_doc_answer", on_delete=models.CASCADE, null=True, blank=True)
    document = models.ForeignKey(UserUploads, related_name="property_evaluator_doc_answer_document", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="property_evaluator_doc_answer_user", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "property_evaluator_doc_answer"


class PropertyOpening(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_opening_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="property_opening_property", on_delete=models.CASCADE)
    opening_start_date = models.DateTimeField(null=True, blank=True)
    opening_end_date = models.DateTimeField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_opening_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_opening"


class PropertyWatcher(Default):
    user = models.ForeignKey(Users, related_name="property_watcher_user", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="property_watcher_property", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_watcher"


class PropertyEvaluatorSetting(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="property_evaluator_setting_domain", on_delete=models.CASCADE)
    property_type = models.ForeignKey(LookupPropertyAsset, related_name="property_evaluator_setting_property_type", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="property_evaluator_setting_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_evaluator_setting"


class SaveSearch(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="save_search_domain", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=251, null=True, blank=True)
    parameters = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="save_search_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "save_search"


class Portfolio(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="portfolio_domain", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="portfolio_user", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=251, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    terms = models.TextField(null=True, blank=True)
    contact = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="portfolio_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "portfolio"


class PropertyPortfolio(Default):
    portfolio = models.ForeignKey(Portfolio, related_name="property_portfolio", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="property_portfolio_property", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="property_portfolio_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_portfolio"


class PropertyPortfolioImages(Default):
    portfolio = models.ForeignKey(Portfolio, related_name="property_portfolio_images", on_delete=models.CASCADE, null=True, blank=True)
    upload = models.ForeignKey(UserUploads, related_name="property_portfolio_images_upload", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="property_portfolio_images_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "property_portfolio_images"


class IdxPropertyUploads(Default):
    upload = models.CharField(max_length=255, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="property_idx_property_uploads", on_delete=models.CASCADE)
    upload_type = models.IntegerField(choices=((1, "Images"), (2, "Video"), (3, "Documents")))
    status = models.ForeignKey(LookupStatus, related_name="idx_property_uploads_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "idx_property_uploads"
