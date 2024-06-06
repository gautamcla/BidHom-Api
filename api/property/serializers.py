# -*- coding: utf-8 -*-
"""Property Serializer

"""
from rest_framework import serializers
from api.property.models import *
from api.advertisement.models import *
from api.bid.models import *
from django.db.models import F
from django.db.models import Q
from django.db.models import Count
from django.conf import settings
from django.utils import timezone


class AddPropertySerializer(serializers.ModelSerializer):
    """
    AddPropertySerializer
    """

    class Meta:
        model = PropertyListing
        fields = "__all__"


class PropertyListingSerializer(serializers.ModelSerializer):
    """
    PropertyListingSerializer
    """
    name = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    approval = serializers.SerializerMethodField()
    no_view = serializers.SerializerMethodField()
    broker_name = serializers.SerializerMethodField()
    property_location = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="property_asset.name", read_only=True, default="")
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    bidder_offer_count = serializers.SerializerMethodField()
    # english_auction_end_time = serializers.SerializerMethodField()
    open_house_start = serializers.SerializerMethodField()
    open_house_end = serializers.SerializerMethodField()
    no_watcher = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "name", "auction_type", "company_name", "bids", "bidding_start", "bidding_end", "created_date",
                  "status", "approval", "no_view", "broker_name", "property_location", "property_image", "property_type",
                  "status_id", "is_approved", "domain_url", "sale_by_type", "bidder_offer_count", "open_house_start",
                  "open_house_end", "no_watcher", "domain", "agent_id", "idx_property_id", "idx_property_image")



    @staticmethod
    def get_name(obj):
        try:
            name = obj.address_one
            name += ", "+obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.agent.user_business_profile.first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_bids(obj):
        try:
            return obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_created_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_approval(obj):
        try:
            return "Approved" if obj.is_approved is not None and obj.is_approved == 1 else "Not Approved"
        except Exception as exp:
            return ""

    @staticmethod
    def get_no_view(obj):
        try:
            # return obj.property_watcher_property.count()
            return obj.property_view_property.count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_broker_name(obj):
        try:
            data = obj.agent.user_business_profile.first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_location(obj):
        try:
            name = obj.city
            name += ", " + obj.state.state_name if obj.state is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bidder_offer_count(obj):
        try:
            if obj.sale_by_type_id == 4 or obj.sale_by_type_id == 7:
                return obj.master_offer_property.exclude(status__in=[2, 5]).count()
            else:
                return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_open_house_start(obj):
        try:
            return obj.property_opening_property.first().opening_start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_open_house_end(obj):
        try:
            return obj.property_opening_property.first().opening_end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_no_watcher(obj):
        try:
            return obj.property_watcher_property.count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_domain(obj):
        try:
            return obj.agent.site_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                data = obj.property_idx_property_uploads.filter(status=1).first()
                all_data = {"id": data.id, "upload": data.upload}
                return all_data
            else:
                return {}
        except Exception as exp:
            return {}


class AdminPropertyListingSerializer(serializers.ModelSerializer):
    """
    AdminPropertyListingSerializer
    """
    name = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    bids = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    approval = serializers.SerializerMethodField()
    no_view = serializers.SerializerMethodField()
    broker_name = serializers.SerializerMethodField()
    property_location = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")
    bidder_offer_count = serializers.SerializerMethodField()
    favourite_count = serializers.SerializerMethodField()
    bid_increment = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "name", "address_one", "postal_code", "auction_type", "company_name", "bids", "bidding_start", "bidding_end", "created_date",
                  "status", "approval", "no_view", "broker_name", "property_location", "property_image", "domain_url",
                  "status_id", "is_approved", "bidder_offer_count", "sale_by_type", "favourite_count", "bid_increment")

    
    @staticmethod
    def get_bid_increment(obj):
        try:
            data = obj.property_auction.first()
            return data.bid_increments if data.bid_increments is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_name(obj):
        try:
            name = obj.address_one
            name += ", "+obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_name(obj):
        try:
            return obj.agent.user_business_profile.first().company_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_bids(obj):
        try:
            return obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_created_date(obj):
        try:
            return obj.added_on
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_approval(obj):
        try:
            return "Approved" if obj.is_approved is not None and obj.is_approved == 1 else "Not Approved"
        except Exception as exp:
            return ""

    @staticmethod
    def get_no_view(obj):
        try:
            return obj.property_watcher_property.count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_broker_name(obj):
        try:
            data = obj.agent.user_business_profile.first()
            return data.first_name + " " + data.last_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_location(obj):
        try:
            name = obj.city
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bidder_offer_count(obj):
        try:
            if obj.sale_by_type_id == 4 or obj.sale_by_type_id == 7:
                return obj.master_offer_property.exclude(status__in=[2, 5]).count()
            else:
                return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_favourite_count(obj):
        try:
            return obj.property_favourite_property.count()
        except Exception as exp:
            return 0


class PropertyDetailStepOneSerializer(serializers.ModelSerializer):
    """
    PropertyDetailStepOneSerializer
    """
    asset_id = serializers.SerializerMethodField()
    property_subtype = serializers.SerializerMethodField()
    terms_accepted = serializers.SerializerMethodField()
    occupied_by = serializers.SerializerMethodField()
    ownership = serializers.SerializerMethodField()
    possession = serializers.SerializerMethodField()
    style = serializers.SerializerMethodField()
    cooling = serializers.SerializerMethodField()
    stories = serializers.SerializerMethodField()
    heating = serializers.SerializerMethodField()
    electric = serializers.SerializerMethodField()
    gas = serializers.SerializerMethodField()
    recent_updates = serializers.SerializerMethodField()
    water = serializers.SerializerMethodField()
    security_features = serializers.SerializerMethodField()
    sewer = serializers.SerializerMethodField()
    tax_exemptions = serializers.SerializerMethodField()
    zoning = serializers.SerializerMethodField()
    hoa_amenities = serializers.SerializerMethodField()
    kitchen_features = serializers.SerializerMethodField()
    appliances = serializers.SerializerMethodField()
    flooring = serializers.SerializerMethodField()
    windows = serializers.SerializerMethodField()
    bedroom_features = serializers.SerializerMethodField()
    other_rooms = serializers.SerializerMethodField()
    bathroom_features = serializers.SerializerMethodField()
    other_features = serializers.SerializerMethodField()
    master_bedroom_features = serializers.SerializerMethodField()
    fireplace_type = serializers.SerializerMethodField()
    basement_features = serializers.SerializerMethodField()
    handicap_amenities = serializers.SerializerMethodField()
    construction = serializers.SerializerMethodField()
    garage_parking = serializers.SerializerMethodField()
    exterior_features = serializers.SerializerMethodField()
    garage_features = serializers.SerializerMethodField()
    roof = serializers.SerializerMethodField()
    outbuildings = serializers.SerializerMethodField()
    foundation = serializers.SerializerMethodField()
    location_features = serializers.SerializerMethodField()
    fence = serializers.SerializerMethodField()
    road_frontage = serializers.SerializerMethodField()
    pool = serializers.SerializerMethodField()
    property_faces = serializers.SerializerMethodField()
    lease_type = serializers.SerializerMethodField()
    tenant_pays = serializers.SerializerMethodField()
    inclusions = serializers.SerializerMethodField()
    building_class = serializers.SerializerMethodField()
    interior_features = serializers.SerializerMethodField()
    mineral_rights = serializers.SerializerMethodField()
    easements = serializers.SerializerMethodField()
    survey = serializers.SerializerMethodField()
    utilities = serializers.SerializerMethodField()
    improvements = serializers.SerializerMethodField()
    topography = serializers.SerializerMethodField()
    wildlife = serializers.SerializerMethodField()
    fish = serializers.SerializerMethodField()
    irrigation_system = serializers.SerializerMethodField()
    recreation = serializers.SerializerMethodField()
    property_auction_data = serializers.SerializerMethodField()
    description_image = serializers.SerializerMethodField()
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_opening_dates = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "asset_id", "property_type", "broker_co_op",
                  "property_subtype", "terms_accepted", "beds", "baths", "occupied_by", "year_built", "year_renovated",
                  "ownership", "square_footage", "possession", "lot_size", "lot_size_unit_id", "home_warranty",
                  "lot_dimensions", "style", "cooling", "stories", "heating", "garage_spaces", "electric", "basement",
                  "gas", "recent_updates", "water", "security_features", "sewer", "property_taxes",
                  "special_assessment_tax", "county", "tax_exemptions", "zoning", "hoa_fee", "hoa_fee_type",
                  "subdivision", "hoa_amenities", "school_district", "upper_floor_area", "main_floor_area",
                  "basement_area", "upper_floor_bedroom", "main_floor_bedroom", "basement_bedroom",
                  "upper_floor_bathroom", "main_floor_bathroom", "basement_bathroom", "kitchen_features", "appliances",
                  "flooring", "windows", "bedroom_features", "other_rooms", "bathroom_features", "other_features",
                  "master_bedroom_features", "fireplace", "fireplace_type", "basement_features", "handicap_amenities",
                  "construction", "garage_parking", "exterior_features", "garage_features", "roof", "outbuildings",
                  "foundation", "location_features", "fence", "road_frontage", "pool", "property_faces", "lease_type",
                  "tenant_pays", "inclusions", "building_class", "interior_features", "mineral_rights", "easements",
                  "survey", "utilities", "improvements", "topography", "wildlife", "fish", "irrigation_system",
                  "recreation", "lease_expiration", "total_buildings", "total_units", "net_operating_income",
                  "occupancy", "total_floors", "garage_spaces", "cap_rate", "average_monthly_rate", "total_rooms",
                  "total_bedrooms", "total_bathrooms", "total_public_restrooms", "ceiling_height", "total_acres",
                  "dryland_acres", "irrigated_acres", "grass_acres", "pasture_fenced_acres", "crp_acres", "timber_acres",
                  "lot_acres", "balance_other_acres", "fsa_information", "crop_yield_history", "ponds", "wells",
                  "soil_productivity_rating", "livestock_carrying_capacity", "annual_payment", "contract_expire",
                  "property_auction_data", "sale_terms", "sale_by_type", "description", "is_featured", "status",
                  "description_image", "state_name", "property_opening_dates", "auction_location", "closing_status",
                  "due_diligence_period", "escrow_period", "earnest_deposit", "earnest_deposit_type",
                  "highest_best_format", "financing_available", "country", "buyers_premium", "buyers_premium_percentage",
                  "buyers_premium_min_amount", "is_deposit_required", "deposit_amount")

    @staticmethod
    def get_asset_id(obj):
        try:
            return obj.property_asset_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_subtype(obj):
        try:
            return obj.property_subtype.values(feature_id=F("subtype_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_terms_accepted(obj):
        try:
            return obj.property_term_accepted.values(feature_id=F("term_accepted_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_occupied_by(obj):
        try:
            return obj.property_occupied_by.values(feature_id=F("occupied_by_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_ownership(obj):
        try:
            return obj.property_ownership.values(feature_id=F("ownership_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_possession(obj):
        try:
            return obj.property_possession.values(feature_id=F("possession_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_style(obj):
        try:
            return obj.property_style.values(feature_id=F("style_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_cooling(obj):
        try:
            return obj.property_cooling.values(feature_id=F("cooling_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_stories(obj):
        try:
            return obj.property_stories.values(feature_id=F("stories_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_heating(obj):
        try:
            return obj.property_heating.values(feature_id=F("heating_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_electric(obj):
        try:
            return obj.property_electric.values(feature_id=F("electric_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_gas(obj):
        try:
            return obj.property_gas.values(feature_id=F("gas_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recent_updates(obj):
        try:
            return obj.property_recent_updates.values(feature_id=F("recent_updates_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_water(obj):
        try:
            return obj.property_water.values(feature_id=F("water_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_security_features(obj):
        try:
            return obj.property_security_features.values(feature_id=F("security_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_sewer(obj):
        try:
            return obj.property_sewer.values(feature_id=F("sewer_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tax_exemptions(obj):
        try:
            return obj.property_tax_exemptions.values(feature_id=F("tax_exemptions_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_zoning(obj):
        try:
            return obj.property_zoning.values(feature_id=F("zoning_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_hoa_amenities(obj):
        try:
            return obj.property_amenities.values(feature_id=F("amenities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_kitchen_features(obj):
        try:
            return obj.property_kitchen_features.values(feature_id=F("kitchen_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_appliances(obj):
        try:
            return obj.property_appliances.values(feature_id=F("appliances_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_flooring(obj):
        try:
            return obj.property_flooring.values(feature_id=F("flooring_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_windows(obj):
        try:
            return obj.property_windows.values(feature_id=F("windows_id"))
        except Exception as exp:
            return []

    # "bedroom_features", "other_rooms", "bathroom_features", "other_features", "master_bedroom_features"

    @staticmethod
    def get_bedroom_features(obj):
        try:
            return obj.property_bedroom_features.values(feature_id=F("bedroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_rooms(obj):
        try:
            return obj.property_other_rooms.values(feature_id=F("other_rooms_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_bathroom_features(obj):
        try:
            return obj.property_bathroom_features.values(feature_id=F("bathroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_features(obj):
        try:
            return obj.property_other_features.values(feature_id=F("other_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_master_bedroom_features(obj):
        try:
            return obj.property_master_bedroom_features.values(feature_id=F("master_bedroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fireplace_type(obj):
        try:
            return obj.property_fireplace_type.values(feature_id=F("fireplace_type_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_basement_features(obj):
        try:
            return obj.property_basement_features.values(feature_id=F("basement_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_handicap_amenities(obj):
        try:
            return obj.property_handicap_amenities.values(feature_id=F("handicap_amenities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_construction(obj):
        try:
            return obj.property_construction.values(feature_id=F("construction_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_parking(obj):
        try:
            return obj.property_garage_parking.values(feature_id=F("garage_parking_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_exterior_features(obj):
        try:
            return obj.property_exterior_features.values(feature_id=F("exterior_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_features(obj):
        try:
            return obj.property_garage_features.values(feature_id=F("garage_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_roof(obj):
        try:
            return obj.property_roof.values(feature_id=F("roof_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_outbuildings(obj):
        try:
            return obj.property_outbuildings.values(feature_id=F("outbuildings_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_foundation(obj):
        try:
            return obj.property_foundation.values(feature_id=F("foundation_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_location_features(obj):
        try:
            return obj.property_location_features.values(feature_id=F("location_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fence(obj):
        try:
            return obj.property_fence.values(feature_id=F("fence_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_road_frontage(obj):
        try:
            return obj.property_road_frontage.values(feature_id=F("road_frontage_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_pool(obj):
        try:
            return obj.property_pool.values(feature_id=F("pool_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_faces(obj):
        try:
            return obj.property_property_faces.values(feature_id=F("property_faces_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_lease_type(obj):
        try:
            return obj.property_lease_type.values(feature_id=F("lease_type_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tenant_pays(obj):
        try:
            return obj.property_tenant_pays.values(feature_id=F("tenant_pays_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_inclusions(obj):
        try:
            return obj.property_inclusions.values(feature_id=F("inclusions_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_building_class(obj):
        try:
            return obj.property_building_class.values(feature_id=F("building_class_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_interior_features(obj):
        try:
            return obj.property_interior_features.values(feature_id=F("interior_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_mineral_rights(obj):
        try:
            return obj.property_mineral_rights.values(feature_id=F("mineral_rights_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_easements(obj):
        try:
            return obj.property_easements.values(feature_id=F("easements_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_survey(obj):
        try:
            return obj.property_survey.values(feature_id=F("survey_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_utilities(obj):
        try:
            return obj.property_utilities.values(feature_id=F("utilities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_improvements(obj):
        try:
            return obj.property_improvements.values(feature_id=F("improvements_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_topography(obj):
        try:
            return obj.property_topography.values(feature_id=F("topography_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_wildlife(obj):
        try:
            return obj.property_wildlife.values(feature_id=F("wildlife_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fish(obj):
        try:
            return obj.property_fish.values(feature_id=F("fish_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_irrigation_system(obj):
        try:
            return obj.property_irrigation_system.values(feature_id=F("irrigation_system_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recreation(obj):
        try:
            return obj.property_recreation.values(feature_id=F("recreation_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_auction_data(obj):
        try:
            data = obj.property_auction.values("id", "property_id", "start_date", "end_date", "bid_increments",
                                               "reserve_amount", "status_id", "time_zone", "start_price", "offer_amount",
                                               "open_house_start_date", "open_house_end_date", 'un_priced',
                                               "required_all", "insider_price_decrease", "dutch_time", "dutch_end_time",
                                               "dutch_pause_time", "sealed_time", "sealed_start_time", "sealed_end_time",
                                               "sealed_pause_time", "english_time", "english_start_time", auction_status=F("status_id"))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_description_image(obj):
        try:
            try:
                data = obj.property_uploads_property.filter(upload_type=1).first()
                all_data = {
                    "upload_id": data.upload.id,
                    "doc_file_name": data.upload.doc_file_name,
                    "bucket_name": data.upload.bucket_name
                }
                return all_data
            except Exception as exp:
                return []
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_opening_dates(obj):
        try:
            return obj.property_opening_property.filter(status=1).values("id", "opening_start_date", "opening_end_date")
        except Exception as exp:
            return []


class PropertyDetailStepTwoSerializer(serializers.ModelSerializer):
    """
    PropertyDetailStepTwoSerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "is_map_view", "is_street_view", "is_arial_view", "address_one", "address_two", "city", "state", "postal_code", "map_url", "latitude",
                  "longitude")


class PropertyDetailStepThreeSerializer(serializers.ModelSerializer):
    """
    PropertyDetailStepThreeSerializer
    """
    photo = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "photo", "video")

    @staticmethod
    def get_photo(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=1).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_video(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=2).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class PropertyDetailStepFourSerializer(serializers.ModelSerializer):
    """
    PropertyDetailStepFourSerializer
    """
    documents = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "documents")

    @staticmethod
    def get_documents(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=3).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class AdminPropertyDetailStepOneSerializer(serializers.ModelSerializer):
    """
    AdminPropertyDetailStepOneSerializer
    """
    asset_id = serializers.SerializerMethodField()
    property_subtype = serializers.SerializerMethodField()
    terms_accepted = serializers.SerializerMethodField()
    occupied_by = serializers.SerializerMethodField()
    ownership = serializers.SerializerMethodField()
    possession = serializers.SerializerMethodField()
    style = serializers.SerializerMethodField()
    cooling = serializers.SerializerMethodField()
    stories = serializers.SerializerMethodField()
    heating = serializers.SerializerMethodField()
    electric = serializers.SerializerMethodField()
    gas = serializers.SerializerMethodField()
    recent_updates = serializers.SerializerMethodField()
    water = serializers.SerializerMethodField()
    security_features = serializers.SerializerMethodField()
    sewer = serializers.SerializerMethodField()
    tax_exemptions = serializers.SerializerMethodField()
    zoning = serializers.SerializerMethodField()
    hoa_amenities = serializers.SerializerMethodField()
    kitchen_features = serializers.SerializerMethodField()
    appliances = serializers.SerializerMethodField()
    flooring = serializers.SerializerMethodField()
    windows = serializers.SerializerMethodField()
    bedroom_features = serializers.SerializerMethodField()
    other_rooms = serializers.SerializerMethodField()
    bathroom_features = serializers.SerializerMethodField()
    other_features = serializers.SerializerMethodField()
    master_bedroom_features = serializers.SerializerMethodField()
    fireplace_type = serializers.SerializerMethodField()
    basement_features = serializers.SerializerMethodField()
    handicap_amenities = serializers.SerializerMethodField()
    construction = serializers.SerializerMethodField()
    garage_parking = serializers.SerializerMethodField()
    exterior_features = serializers.SerializerMethodField()
    garage_features = serializers.SerializerMethodField()
    roof = serializers.SerializerMethodField()
    outbuildings = serializers.SerializerMethodField()
    foundation = serializers.SerializerMethodField()
    location_features = serializers.SerializerMethodField()
    fence = serializers.SerializerMethodField()
    road_frontage = serializers.SerializerMethodField()
    pool = serializers.SerializerMethodField()
    property_faces = serializers.SerializerMethodField()
    lease_type = serializers.SerializerMethodField()
    tenant_pays = serializers.SerializerMethodField()
    inclusions = serializers.SerializerMethodField()
    building_class = serializers.SerializerMethodField()
    interior_features = serializers.SerializerMethodField()
    mineral_rights = serializers.SerializerMethodField()
    easements = serializers.SerializerMethodField()
    survey = serializers.SerializerMethodField()
    utilities = serializers.SerializerMethodField()
    improvements = serializers.SerializerMethodField()
    topography = serializers.SerializerMethodField()
    wildlife = serializers.SerializerMethodField()
    fish = serializers.SerializerMethodField()
    irrigation_system = serializers.SerializerMethodField()
    recreation = serializers.SerializerMethodField()
    property_auction_data = serializers.SerializerMethodField()
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_opening_dates = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "domain", "agent", "is_featured", "address_one", "city", "state", "postal_code", "asset_id", "property_type", "broker_co_op",
                  "property_subtype", "terms_accepted", "beds", "baths", "occupied_by", "year_built", "year_renovated",
                  "ownership", "square_footage", "possession", "lot_size", "lot_size_unit_id", "home_warranty",
                  "lot_dimensions", "style", "cooling", "stories", "heating", "garage_spaces", "electric", "basement",
                  "gas", "recent_updates", "water", "security_features", "sewer", "property_taxes",
                  "special_assessment_tax", "county", "tax_exemptions", "zoning", "hoa_fee", "hoa_fee_type",
                  "subdivision", "hoa_amenities", "school_district", "upper_floor_area", "main_floor_area",
                  "basement_area", "upper_floor_bedroom", "main_floor_bedroom", "basement_bedroom",
                  "upper_floor_bathroom", "main_floor_bathroom", "basement_bathroom", "kitchen_features", "appliances",
                  "flooring", "windows", "bedroom_features", "other_rooms", "bathroom_features", "other_features",
                  "master_bedroom_features", "fireplace", "fireplace_type", "basement_features", "handicap_amenities",
                  "construction", "garage_parking", "exterior_features", "garage_features", "roof", "outbuildings",
                  "foundation", "location_features", "fence", "road_frontage", "pool", "property_faces", "lease_type",
                  "tenant_pays", "inclusions", "building_class", "interior_features", "mineral_rights", "easements",
                  "survey", "utilities", "improvements", "topography", "wildlife", "fish", "irrigation_system",
                  "recreation", "lease_expiration", "total_buildings", "total_units", "net_operating_income",
                  "occupancy", "total_floors", "garage_spaces", "cap_rate", "average_monthly_rate", "total_rooms",
                  "total_bedrooms", "total_bathrooms", "total_public_restrooms", "ceiling_height", "total_acres",
                  "dryland_acres", "irrigated_acres", "grass_acres", "pasture_fenced_acres", "crp_acres", "timber_acres",
                  "lot_acres", "balance_other_acres", "fsa_information", "crop_yield_history", "ponds", "wells",
                  "soil_productivity_rating", "livestock_carrying_capacity", "annual_payment", "contract_expire",
                  "property_auction_data", "sale_terms", "sale_by_type", "description", "status", "state_name",
                  "property_opening_dates", "auction_location", "closing_status", "due_diligence_period",
                  "escrow_period", "earnest_deposit", "earnest_deposit_type", "highest_best_format", "financing_available")

    @staticmethod
    def get_asset_id(obj):
        try:
            return obj.property_asset_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_subtype(obj):
        try:
            return obj.property_subtype.values(feature_id=F("subtype_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_terms_accepted(obj):
        try:
            return obj.property_term_accepted.values(feature_id=F("term_accepted_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_occupied_by(obj):
        try:
            return obj.property_occupied_by.values(feature_id=F("occupied_by_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_ownership(obj):
        try:
            return obj.property_ownership.values(feature_id=F("ownership_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_possession(obj):
        try:
            return obj.property_possession.values(feature_id=F("possession_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_style(obj):
        try:
            return obj.property_style.values(feature_id=F("style_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_cooling(obj):
        try:
            return obj.property_cooling.values(feature_id=F("cooling_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_stories(obj):
        try:
            return obj.property_stories.values(feature_id=F("stories_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_heating(obj):
        try:
            return obj.property_heating.values(feature_id=F("heating_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_electric(obj):
        try:
            return obj.property_electric.values(feature_id=F("electric_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_gas(obj):
        try:
            return obj.property_gas.values(feature_id=F("gas_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recent_updates(obj):
        try:
            return obj.property_recent_updates.values(feature_id=F("recent_updates_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_water(obj):
        try:
            return obj.property_water.values(feature_id=F("water_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_security_features(obj):
        try:
            return obj.property_security_features.values(feature_id=F("security_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_sewer(obj):
        try:
            return obj.property_sewer.values(feature_id=F("sewer_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tax_exemptions(obj):
        try:
            return obj.property_tax_exemptions.values(feature_id=F("tax_exemptions_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_zoning(obj):
        try:
            return obj.property_zoning.values(feature_id=F("zoning_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_hoa_amenities(obj):
        try:
            return obj.property_amenities.values(feature_id=F("amenities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_kitchen_features(obj):
        try:
            return obj.property_kitchen_features.values(feature_id=F("kitchen_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_appliances(obj):
        try:
            return obj.property_appliances.values(feature_id=F("appliances_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_flooring(obj):
        try:
            return obj.property_flooring.values(feature_id=F("flooring_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_windows(obj):
        try:
            return obj.property_windows.values(feature_id=F("windows_id"))
        except Exception as exp:
            return []

    # "bedroom_features", "other_rooms", "bathroom_features", "other_features", "master_bedroom_features"

    @staticmethod
    def get_bedroom_features(obj):
        try:
            return obj.property_bedroom_features.values(feature_id=F("bedroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_rooms(obj):
        try:
            return obj.property_other_rooms.values(feature_id=F("other_rooms_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_bathroom_features(obj):
        try:
            return obj.property_bathroom_features.values(feature_id=F("bathroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_features(obj):
        try:
            return obj.property_other_features.values(feature_id=F("other_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_master_bedroom_features(obj):
        try:
            return obj.property_master_bedroom_features.values(feature_id=F("master_bedroom_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fireplace_type(obj):
        try:
            return obj.property_fireplace_type.values(feature_id=F("fireplace_type_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_basement_features(obj):
        try:
            return obj.property_basement_features.values(feature_id=F("basement_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_handicap_amenities(obj):
        try:
            return obj.property_handicap_amenities.values(feature_id=F("handicap_amenities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_construction(obj):
        try:
            return obj.property_construction.values(feature_id=F("construction_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_parking(obj):
        try:
            return obj.property_garage_parking.values(feature_id=F("garage_parking_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_exterior_features(obj):
        try:
            return obj.property_exterior_features.values(feature_id=F("exterior_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_features(obj):
        try:
            return obj.property_garage_features.values(feature_id=F("garage_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_roof(obj):
        try:
            return obj.property_roof.values(feature_id=F("roof_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_outbuildings(obj):
        try:
            return obj.property_outbuildings.values(feature_id=F("outbuildings_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_foundation(obj):
        try:
            return obj.property_foundation.values(feature_id=F("foundation_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_location_features(obj):
        try:
            return obj.property_location_features.values(feature_id=F("location_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fence(obj):
        try:
            return obj.property_fence.values(feature_id=F("fence_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_road_frontage(obj):
        try:
            return obj.property_road_frontage.values(feature_id=F("road_frontage_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_pool(obj):
        try:
            return obj.property_pool.values(feature_id=F("pool_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_faces(obj):
        try:
            return obj.property_property_faces.values(feature_id=F("property_faces_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_lease_type(obj):
        try:
            return obj.property_lease_type.values(feature_id=F("lease_type_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tenant_pays(obj):
        try:
            return obj.property_tenant_pays.values(feature_id=F("tenant_pays_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_inclusions(obj):
        try:
            return obj.property_inclusions.values(feature_id=F("inclusions_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_building_class(obj):
        try:
            return obj.property_building_class.values(feature_id=F("building_class_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_interior_features(obj):
        try:
            return obj.property_interior_features.values(feature_id=F("interior_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_mineral_rights(obj):
        try:
            return obj.property_mineral_rights.values(feature_id=F("mineral_rights_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_easements(obj):
        try:
            return obj.property_easements.values(feature_id=F("easements_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_survey(obj):
        try:
            return obj.property_survey.values(feature_id=F("survey_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_utilities(obj):
        try:
            return obj.property_utilities.values(feature_id=F("utilities_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_improvements(obj):
        try:
            return obj.property_improvements.values(feature_id=F("improvements_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_topography(obj):
        try:
            return obj.property_topography.values(feature_id=F("topography_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_wildlife(obj):
        try:
            return obj.property_wildlife.values(feature_id=F("wildlife_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fish(obj):
        try:
            return obj.property_fish.values(feature_id=F("fish_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_irrigation_system(obj):
        try:
            return obj.property_irrigation_system.values(feature_id=F("irrigation_system_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recreation(obj):
        try:
            return obj.property_recreation.values(feature_id=F("recreation_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_auction_data(obj):
        try:
            data = obj.property_auction.values("id", "property_id", "start_date", "end_date", "bid_increments",
                                               "reserve_amount", "status_id", "time_zone", "start_price", "offer_amount",
                                               "open_house_start_date", "open_house_end_date", 'un_priced',
                                               'required_all', "insider_price_decrease", "dutch_time", "dutch_end_time",
                                               "dutch_pause_time", "sealed_time", "sealed_start_time", "sealed_end_time",
                                               "sealed_pause_time", "english_time", "english_start_time", auction_status=F("status_id"))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_opening_dates(obj):
        try:
            return obj.property_opening_property.filter(status=1).values("id", "opening_start_date", "opening_end_date")
        except Exception as exp:
            return []


class AdminPropertyDetailStepTwoSerializer(serializers.ModelSerializer):
    """
    AdminPropertyDetailStepTwoSerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "is_map_view", "is_street_view", "is_arial_view", "address_one", "address_two", "city", "state", "postal_code", "map_url", "latitude", "longitude")


class AdminPropertyDetailStepThreeSerializer(serializers.ModelSerializer):
    """
    AdminPropertyDetailStepThreeSerializer
    """
    photo = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "photo", "video")

    @staticmethod
    def get_photo(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=1).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_video(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=2).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class AdminPropertyDetailStepFourSerializer(serializers.ModelSerializer):
    """
    AdminPropertyDetailStepFourSerializer
    """
    documents = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "documents")

    @staticmethod
    def get_documents(obj):
        try:
            return obj.property_uploads_property.filter(upload_type=3).values("upload_id", "added_on", file_size=F("upload__file_size"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class FrontPropertyListingSerializer(serializers.ModelSerializer):
    """
    FrontPropertyListingSerializer
    """
    name = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    property_price = serializers.SerializerMethodField()
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_asset = serializers.CharField(source="property_asset.name", read_only=True, default="")
    is_favourite = serializers.SerializerMethodField()
    bidder_offer_count = serializers.SerializerMethodField()
    iso_state_name = serializers.CharField(source="state.iso_name", read_only=True, default="")
    status_id = serializers.IntegerField(source="status.id", read_only=True, default="")
    closing_status_name = serializers.CharField(source="closing_status.status_name", read_only=True, default="")
    property_current_price = serializers.SerializerMethodField()
    un_priced = serializers.SerializerMethodField()
    current_best_offer = serializers.SerializerMethodField()
    is_multiple_parcel = serializers.SerializerMethodField()
    no_lots = serializers.SerializerMethodField()
    parcel_id = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()
    new_today = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "name", "auction_type", "bidding_start", "bidding_end", "status", "property_image",
                  "property_price", "is_featured", "city", "state_name", "postal_code", "property_asset",
                  "sale_by_type", "address_one", "is_favourite", "bidder_offer_count", "iso_state_name", "added_on",
                  "status_id", "closing_status", "closing_status_name", "property_current_price", "un_priced",
                  "due_diligence_period", "escrow_period", "earnest_deposit", "earnest_deposit_type",
                  "current_best_offer", "highest_best_format", "latitude", "longitude", "is_multiple_parcel",
                  "no_lots", "parcel_id", "idx_property_id", "idx_property_image", "new_today")

    @staticmethod
    def get_name(obj):
        try:
            name = obj.address_one
            name += ", "+obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_location(obj):
        try:
            name = obj.city
            name += ", " + obj.state.state_name if obj.state is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_price(obj):
        try:
            return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_is_favourite(self, obj):
        try:
            user_id = self.context['user_id']
            if user_id is not None:
                data = obj.property_favourite_property.filter(domain=obj.domain_id, property=obj.id, user=user_id).first()
                if data is not None:
                    return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bidder_offer_count(obj):
        try:
            return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_property_current_price(obj):
        try:
            bid = obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if obj.sale_by_type_id not in [4, 7] and bid is not None:
                return bid.bid_amount
            else:
                return 0
        except Exception as exp:
            return ""

    @staticmethod
    def get_un_priced(obj):
        try:
            return obj.property_auction.first().un_priced
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_best_offer(obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, status=1).order_by("offer_price").last()
            return offer_data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_multiple_parcel(obj):
        try:
            portfolio = Portfolio.objects.filter(domain=obj.domain_id, property_portfolio__property=obj.id, status=1).count()
            return True if portfolio > 0 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_no_lots(obj):
        try:
            portfolio = Portfolio.objects.filter(domain=obj.domain_id, property_portfolio__property=obj.id, status=1).first()
            total_cnt = PropertyPortfolio.objects.filter(portfolio__domain=obj.domain_id, portfolio=portfolio.id, status=1).count()
            return total_cnt if total_cnt > 0 else 0
        except Exception as exp:
            return 0

    @staticmethod
    def get_parcel_id(obj):
        try:
            portfolio = Portfolio.objects.filter(domain=obj.domain_id, property_portfolio__property=obj.id, status=1).first()
            return portfolio.id if portfolio is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                data = obj.property_idx_property_uploads.filter(status=1).first()
                all_data = {"id": data.id, "upload": data.upload}
                return all_data
            else:
                return {}
        except Exception as exp:
            return {}

    @staticmethod
    def get_new_today(obj):
        try:
            if obj.added_on.date() == timezone.now().date(): 
                return True
            else:
                return False
        except Exception as exp:
            return False        


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    PropertyDetailSerializer
    """
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    asset_name = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="property_type.property_type", read_only=True, default="")
    property_subtype = serializers.SerializerMethodField()
    terms_accepted = serializers.SerializerMethodField()
    occupied_by = serializers.SerializerMethodField()
    ownership = serializers.SerializerMethodField()
    possession = serializers.SerializerMethodField()
    style = serializers.SerializerMethodField()
    cooling = serializers.SerializerMethodField()
    stories = serializers.SerializerMethodField()
    heating = serializers.SerializerMethodField()
    electric = serializers.SerializerMethodField()
    gas = serializers.SerializerMethodField()
    recent_updates = serializers.SerializerMethodField()
    water = serializers.SerializerMethodField()
    security_features = serializers.SerializerMethodField()
    sewer = serializers.SerializerMethodField()
    tax_exemptions = serializers.SerializerMethodField()
    zoning = serializers.SerializerMethodField()
    hoa_amenities = serializers.SerializerMethodField()
    kitchen_features = serializers.SerializerMethodField()
    appliances = serializers.SerializerMethodField()
    flooring = serializers.SerializerMethodField()
    windows = serializers.SerializerMethodField()
    bedroom_features = serializers.SerializerMethodField()
    other_rooms = serializers.SerializerMethodField()
    bathroom_features = serializers.SerializerMethodField()
    other_features = serializers.SerializerMethodField()
    master_bedroom_features = serializers.SerializerMethodField()
    fireplace_type = serializers.SerializerMethodField()
    basement_features = serializers.SerializerMethodField()
    handicap_amenities = serializers.SerializerMethodField()
    construction = serializers.SerializerMethodField()
    garage_parking = serializers.SerializerMethodField()
    exterior_features = serializers.SerializerMethodField()
    garage_features = serializers.SerializerMethodField()
    roof = serializers.SerializerMethodField()
    outbuildings = serializers.SerializerMethodField()
    foundation = serializers.SerializerMethodField()
    location_features = serializers.SerializerMethodField()
    fence = serializers.SerializerMethodField()
    road_frontage = serializers.SerializerMethodField()
    pool = serializers.SerializerMethodField()
    property_faces = serializers.SerializerMethodField()
    lease_type = serializers.SerializerMethodField()
    tenant_pays = serializers.SerializerMethodField()
    inclusions = serializers.SerializerMethodField()
    building_class = serializers.SerializerMethodField()
    interior_features = serializers.SerializerMethodField()
    mineral_rights = serializers.SerializerMethodField()
    easements = serializers.SerializerMethodField()
    survey = serializers.SerializerMethodField()
    utilities = serializers.SerializerMethodField()
    improvements = serializers.SerializerMethodField()
    topography = serializers.SerializerMethodField()
    wildlife = serializers.SerializerMethodField()
    fish = serializers.SerializerMethodField()
    irrigation_system = serializers.SerializerMethodField()
    recreation = serializers.SerializerMethodField()
    property_auction_data = serializers.SerializerMethodField()
    listed_by = serializers.SerializerMethodField()
    property_pic = serializers.SerializerMethodField()
    property_video = serializers.SerializerMethodField()
    property_doc = serializers.SerializerMethodField()
    hoa_fee_type = serializers.SerializerMethodField()
    lot_size_unit_id = serializers.SerializerMethodField()
    # sale_by_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    sale_by_type = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    registration_approved = serializers.SerializerMethodField()
    is_watch = serializers.SerializerMethodField()
    advertisement = serializers.SerializerMethodField()
    property_opening_dates = serializers.SerializerMethodField()
    property_current_price = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    iso_state_name = serializers.CharField(source="state.iso_name", read_only=True, default="")
    property_status = serializers.CharField(source="status.status_name", read_only=True, default="")
    auction_status = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    my_bid_count = serializers.SerializerMethodField()
    high_bidder_id = serializers.SerializerMethodField()
    property_setting = serializers.SerializerMethodField()
    property_status_id = serializers.IntegerField(source="status.id", read_only=True, default="")
    offer_details = serializers.SerializerMethodField()
    closing_status_name = serializers.CharField(source="closing_status.status_name", read_only=True, default="")
    current_best_offer = serializers.SerializerMethodField()
    is_offer_approved = serializers.SerializerMethodField()
    your_approved_best_offer = serializers.SerializerMethodField()
    is_your_best_offer_accepted = serializers.SerializerMethodField()
    is_last_best_offer_accepted = serializers.SerializerMethodField()
    inline_step = serializers.SerializerMethodField()
    dutch_winning_amount = serializers.SerializerMethodField()
    dutch_winning_user = serializers.SerializerMethodField()
    seal_winning_amount = serializers.SerializerMethodField()
    seal_winning_user = serializers.SerializerMethodField()
    your_seal_amount = serializers.SerializerMethodField()
    total_bid_till_sealed = serializers.SerializerMethodField()
    sealed_user_bid_count = serializers.SerializerMethodField()
    english_user_bid_count = serializers.SerializerMethodField()
    user_current_sealed_bid = serializers.SerializerMethodField()
    registration_id = serializers.SerializerMethodField()
    idx_property_image = serializers.SerializerMethodField()
    buyer_premium_text = serializers.SerializerMethodField()
    new_today = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    is_deposit_required = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "address_one", "city", "state", "postal_code", "asset_name", "property_type", "broker_co_op",
                  "property_subtype", "terms_accepted", "beds", "baths", "occupied_by", "year_built", "year_renovated",
                  "ownership", "square_footage", "possession", "lot_size", "lot_size_unit_id", "home_warranty",
                  "lot_dimensions", "style", "cooling", "stories", "heating", "garage_spaces", "electric", "basement",
                  "gas", "recent_updates", "water", "security_features", "sewer", "property_taxes",
                  "special_assessment_tax", "county", "tax_exemptions", "zoning", "hoa_fee", "hoa_fee_type",
                  "subdivision", "hoa_amenities", "school_district", "upper_floor_area", "main_floor_area",
                  "basement_area", "upper_floor_bedroom", "main_floor_bedroom", "basement_bedroom",
                  "upper_floor_bathroom", "main_floor_bathroom", "basement_bathroom", "kitchen_features", "appliances",
                  "flooring", "windows", "bedroom_features", "other_rooms", "bathroom_features", "other_features",
                  "master_bedroom_features", "fireplace", "fireplace_type", "basement_features", "handicap_amenities",
                  "construction", "garage_parking", "exterior_features", "garage_features", "roof", "outbuildings",
                  "foundation", "location_features", "fence", "road_frontage", "pool", "property_faces", "lease_type",
                  "tenant_pays", "inclusions", "building_class", "interior_features", "mineral_rights", "easements",
                  "survey", "utilities", "improvements", "topography", "wildlife", "fish", "irrigation_system",
                  "recreation", "lease_expiration", "total_buildings", "total_units", "net_operating_income",
                  "occupancy", "total_floors", "garage_spaces", "cap_rate", "average_monthly_rate", "total_rooms",
                  "total_bedrooms", "total_bathrooms", "total_public_restrooms", "ceiling_height", "total_acres",
                  "dryland_acres", "irrigated_acres", "grass_acres", "pasture_fenced_acres", "crp_acres", "timber_acres",
                  "lot_acres", "balance_other_acres", "fsa_information", "crop_yield_history", "ponds", "wells",
                  "soil_productivity_rating", "livestock_carrying_capacity", "annual_payment", "contract_expire",
                  "property_auction_data", "sale_terms", "sale_by_type", "description", "listed_by", "property_pic",
                  "property_video", "property_doc", "property_asset_id", "is_map_view", "is_street_view",
                  "is_arial_view", "sale_by_type_id", "is_registered", "registration_approved", "is_watch",
                  "advertisement", "map_url", "property_opening_dates", "property_current_price", "bid_count",
                  "is_favourite", "iso_state_name", "property_status", "auction_status", "is_approved", "is_reviewed",
                  "my_bid_count", "high_bidder_id", "property_setting", "property_status_id", "added_on", "updated_on",
                  "offer_details", "auction_location", "closing_status", "closing_status_name", "due_diligence_period",
                  "escrow_period", "earnest_deposit", "earnest_deposit_type", "highest_best_format",
                  "current_best_offer", "is_offer_approved", "your_approved_best_offer", "is_your_best_offer_accepted",
                  "is_last_best_offer_accepted", "inline_step", "dutch_winning_amount", "dutch_winning_user",
                  "seal_winning_amount", "seal_winning_user", "your_seal_amount", "total_bid_till_sealed",
                  "sealed_user_bid_count", "english_user_bid_count", "user_current_sealed_bid", "latitude", "longitude",
                  "registration_id", "idx_property_id", "idx_property_image", "buyers_premium",
                  "buyers_premium_percentage", "buyers_premium_min_amount", "buyer_premium_text", "new_today", "bidding_start",
                  "bidding_end", "is_deposit_required", "deposit_amount")

    @staticmethod
    def get_asset_name(obj):
        try:
            return obj.property_asset.name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_subtype(obj):
        try:
            return obj.property_subtype.values(feature_name=F("subtype__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_terms_accepted(obj):
        try:
            return obj.property_term_accepted.values(feature_name=F("term_accepted__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_occupied_by(obj):
        try:
            return obj.property_occupied_by.values(feature_name=F("occupied_by__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_ownership(obj):
        try:
            return obj.property_ownership.values(feature_name=F("ownership__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_possession(obj):
        try:
            return obj.property_possession.values(feature_name=F("possession__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_style(obj):
        try:
            return obj.property_style.values(feature_name=F("style__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_cooling(obj):
        try:
            return obj.property_cooling.values(feature_name=F("cooling__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_stories(obj):
        try:
            return obj.property_stories.values(feature_name=F("stories__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_heating(obj):
        try:
            return obj.property_heating.values(feature_name=F("heating__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_electric(obj):
        try:
            return obj.property_electric.values(feature_name=F("electric__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_gas(obj):
        try:
            return obj.property_gas.values(feature_name=F("gas__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recent_updates(obj):
        try:
            return obj.property_recent_updates.values(feature_name=F("recent_updates__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_water(obj):
        try:
            return obj.property_water.values(feature_name=F("water__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_security_features(obj):
        try:
            return obj.property_security_features.values(feature_name=F("security_features_id"))
        except Exception as exp:
            return []

    @staticmethod
    def get_sewer(obj):
        try:
            return obj.property_sewer.values(feature_name=F("sewer__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tax_exemptions(obj):
        try:
            return obj.property_tax_exemptions.values(feature_name=F("tax_exemptions__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_zoning(obj):
        try:
            return obj.property_zoning.values(feature_name=F("zoning__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_hoa_amenities(obj):
        try:
            return obj.property_amenities.values(feature_name=F("amenities__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_kitchen_features(obj):
        try:
            return obj.property_kitchen_features.values(feature_name=F("kitchen_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_appliances(obj):
        try:
            return obj.property_appliances.values(feature_name=F("appliances__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_flooring(obj):
        try:
            return obj.property_flooring.values(feature_name=F("flooring__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_windows(obj):
        try:
            return obj.property_windows.values(feature_name=F("windows__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_bedroom_features(obj):
        try:
            return obj.property_bedroom_features.values(feature_name=F("bedroom_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_rooms(obj):
        try:
            return obj.property_other_rooms.values(feature_name=F("other_rooms__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_bathroom_features(obj):
        try:
            return obj.property_bathroom_features.values(feature_name=F("bathroom_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_other_features(obj):
        try:
            return obj.property_other_features.values(feature_name=F("other_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_master_bedroom_features(obj):
        try:
            return obj.property_master_bedroom_features.values(feature_name=F("master_bedroom_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fireplace_type(obj):
        try:
            return obj.property_fireplace_type.values(feature_name=F("fireplace_type__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_basement_features(obj):
        try:
            return obj.property_basement_features.values(feature_name=F("basement_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_handicap_amenities(obj):
        try:
            return obj.property_handicap_amenities.values(feature_name=F("handicap_amenities__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_construction(obj):
        try:
            return obj.property_construction.values(feature_name=F("construction__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_parking(obj):
        try:
            return obj.property_garage_parking.values(feature_name=F("garage_parking__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_exterior_features(obj):
        try:
            return obj.property_exterior_features.values(feature_name=F("exterior_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_garage_features(obj):
        try:
            return obj.property_garage_features.values(feature_name=F("garage_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_roof(obj):
        try:
            return obj.property_roof.values(feature_name=F("roof__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_outbuildings(obj):
        try:
            return obj.property_outbuildings.values(feature_name=F("outbuildings__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_foundation(obj):
        try:
            return obj.property_foundation.values(feature_name=F("foundation__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_location_features(obj):
        try:
            return obj.property_location_features.values(feature_name=F("location_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fence(obj):
        try:
            return obj.property_fence.values(feature_name=F("fence__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_road_frontage(obj):
        try:
            return obj.property_road_frontage.values(feature_name=F("road_frontage__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_pool(obj):
        try:
            return obj.property_pool.values(feature_name=F("pool__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_faces(obj):
        try:
            return obj.property_property_faces.values(feature_name=F("property_faces__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_lease_type(obj):
        try:
            return obj.property_lease_type.values(feature_name=F("lease_type__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_tenant_pays(obj):
        try:
            return obj.property_tenant_pays.values(feature_name=F("tenant_pays__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_inclusions(obj):
        try:
            return obj.property_inclusions.values(feature_name=F("inclusions__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_building_class(obj):
        try:
            return obj.property_building_class.values(feature_name=F("building_class__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_interior_features(obj):
        try:
            return obj.property_interior_features.values(feature_name=F("interior_features__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_mineral_rights(obj):
        try:
            return obj.property_mineral_rights.values(feature_name=F("mineral_rights__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_easements(obj):
        try:
            return obj.property_easements.values(feature_name=F("easements__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_survey(obj):
        try:
            return obj.property_survey.values(feature_name=F("survey__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_utilities(obj):
        try:
            return obj.property_utilities.values(feature_name=F("utilities__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_improvements(obj):
        try:
            return obj.property_improvements.values(feature_name=F("improvements__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_topography(obj):
        try:
            return obj.property_topography.values(feature_name=F("topography__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_wildlife(obj):
        try:
            return obj.property_wildlife.values(feature_name=F("wildlife__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_fish(obj):
        try:
            return obj.property_fish.values(feature_name=F("fish__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_irrigation_system(obj):
        try:
            return obj.property_irrigation_system.values(feature_name=F("irrigation_system__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_recreation(obj):
        try:
            return obj.property_recreation.values(feature_name=F("recreation__name"))
        except Exception as exp:
            return []

    @staticmethod
    def get_property_auction_data(obj):
        try:
            data = obj.property_auction.values("id", "start_date", "end_date", "bid_increments", "reserve_amount",
                                               "start_price", "open_house_start_date", "open_house_end_date",
                                               "offer_amount", "un_priced", "dutch_end_time", "dutch_time",
                                               "dutch_pause_time", "sealed_time", "sealed_start_time", "sealed_end_time",
                                               "sealed_pause_time", "english_time", "english_start_time",
                                               "english_end_time", "insider_decreased_price", "auction_id")
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_listed_by(obj):
        try:
            profile_data = {}
            if obj.agent.profile_image is not None:
                profile_image = UserUploads.objects.get(id=int(obj.agent.profile_image))
                profile_data["doc_file_name"] = profile_image.doc_file_name
                profile_data["bucket_name"] = profile_image.bucket_name
            data = {
                "first_name": obj.agent.first_name,
                "last_name": obj.agent.last_name,
                "phone_no": obj.agent.phone_no,
                "profile_image": profile_data,
                "company_name": obj.agent.user_business_profile.first().company_name
            }
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_pic(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1, status=1).values(doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_video(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=2, status=1).values(
                doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_doc(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=3, status=1).values("id", "upload_id",
                                                                                        doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_hoa_fee_type(obj):
        try:
            choices = {1: "Monthly", 2: "Annual"}
            return choices[obj.hoa_fee_type]
        except Exception as exp:
            return ""

    @staticmethod
    def get_lot_size_unit_id(obj):
        try:
            return obj.lot_size_unit.name
        except Exception as exp:
            return ""

    @staticmethod
    def get_sale_by_type(obj):
        try:
            if obj.sale_by_type_id == 4:
                return "Traditional Sale"
            else:
                return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    def get_is_registered(self, obj):
        try:
            data = obj.bid_registration_property.filter(domain=obj.domain_id, user=self.context, status=1).last()
            if data is not None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_registration_approved(self, obj):
        try:
            data = obj.bid_registration_property.filter(domain=obj.domain_id, user=self.context, is_reviewed=1, is_approved=2, status=1).last()
            if data is not None:
                return True
            else:
                return False
        except Exception as exp:
            return False

    def get_is_watch(self, obj):
        try:
            return obj.watch_property_property.filter(user=int(self.context)).count()
        except Exception as exp:
            return False

    @staticmethod
    def get_advertisement(obj):
        try:
            data = Advertisement.objects.filter(Q(domain=obj.domain_id) & Q(status=1))
            if data.count() <= 0:
                data = Advertisement.objects.filter(Q(domain__isnull=True) & Q(status=1))
            data = data.order_by('?').only("id")[0: 3]
            serializer = PropertyAdvertisementSerializer(data, many=True)
            return serializer.data
        except Exception as exp:
            return []

    @staticmethod
    def get_property_opening_dates(obj):
        try:
            return obj.property_opening_property.filter(status=1).values("id", "opening_start_date", "opening_end_date")
        except Exception as exp:
            return []

    @staticmethod
    def get_property_current_price(obj):
        try:
            bid = obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if bid is not None:
                return bid.bid_amount
            else:
                return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_bid_count(obj):
        try:
            return obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).count()
        except Exception as exp:
            return ""

    def get_is_favourite(self, obj):
        try:
            user_id = self.context
            if user_id is not None:
                data = obj.property_favourite_property.filter(domain=obj.domain_id, property=obj.id, user=user_id).first()
                if data is not None:
                    return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_auction_status(obj):
        try:
            return obj.property_auction.first().status_id
        except Exception as exp:
            return False

    def get_is_approved(self, obj):
        try:
            data = obj.bid_registration_property.get(domain=obj.domain_id, user=self.context, status=1)
            return data.is_approved
        except Exception as exp:
            return False

    def get_is_reviewed(self, obj):
        try:
            data = obj.bid_registration_property.get(domain=obj.domain_id, user=self.context, status=1)
            return data.is_reviewed
        except Exception as exp:
            return False

    def get_my_bid_count(self, obj):
        try:
            return obj.bid_property.filter(user=self.context, bid_type__in=[2, 3], is_canceled=0).count()
        except Exception as exp:
            return False

    @staticmethod
    def get_high_bidder_id(obj):
        try:
            return obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_setting(obj):
        try:
            data = {}
            property_setting = obj.property_settings_property.filter(is_broker=0, is_agent=0, status=1).first()
            if property_setting is None:
                # property_setting = obj.property_settings_property.filter(is_broker=0, is_agent=1, status=1).first()
                property_setting = PropertySettings.objects.filter(domain=obj.domain_id, is_broker=0, is_agent=1, status=1).first()
                if property_setting is None:
                    # property_setting = obj.property_settings_property.filter(is_broker=1, is_agent=0, status=1).first()
                    property_setting = PropertySettings.objects.filter(domain=obj.domain_id, is_broker=1, is_agent=0, status=1).first()
            if property_setting is not None:
                data['remain_time_to_add_extension'] = property_setting.remain_time_to_add_extension
                data['log_time_extension'] = property_setting.log_time_extension
                data['auto_approval'] = property_setting.auto_approval
                data['bid_limit'] = property_setting.bid_limit
                data['show_reverse_not_met'] = property_setting.show_reverse_not_met
                data['is_log_time_extension'] = property_setting.is_log_time_extension
                data['time_flash'] = property_setting.time_flash
            else:
                data['remain_time_to_add_extension'] = 0
                data['log_time_extension'] = 0
                data['auto_approval'] = 0
                data['bid_limit'] = 0
                data['show_reverse_not_met'] = 0
                data['is_log_time_extension'] = 0
                data['time_flash'] = 0
            return data
        except Exception as exp:
            return {}

    def get_offer_details(self, obj):
        try:
            all_data = {}
            # data = obj.master_offer_property.filter(user=self.context, status=1).first()
            data = obj.master_offer_property.filter(user=self.context).exclude(status__in=[2, 5]).first()
            if data is not None:
                if obj.sale_by_type_id == 4:
                    last_offer = NegotiatedOffers.objects.filter(master_offer=data.id, status=1).last()
                    # all_data['accepted_by'] = data.accepted_by_id
                else:
                    last_offer = HighestBestNegotiatedOffers.objects.filter(master_offer=data.id, status=1).last()
                    # all_data['accepted_by'] = last_offer.best_offer_accept_by_id
                all_data['accepted_by'] = data.accepted_by_id
                all_data['is_canceled'] = data.is_canceled
                all_data['is_declined'] = data.is_declined
                all_data['status'] = data.status_id
                all_data['declined_by'] = data.declined_by_id
                # all_data['counter_by'] = "" if last_offer.offer_by != 2 else "agent" if last_offer.user_id == last_offer.property.agent_id else "broker"
                all_data['counter_by'] = "Seller" if last_offer is not None and last_offer.offer_by == 2 else "Buyer" if last_offer is not None and last_offer.offer_by == 1 else ""
                all_data['rejected_by'] = "Seller" if data.declined_by_id is not None and data.declined_by_id > 0 and data.final_by == 2 else "Buyer" if data.declined_by_id is not None and data.declined_by_id > 0 and data.final_by == 1 else ""
                # all_data['accepted_by_user'] = "Seller" if data.accepted_by_id is not None and data.accepted_by_id > 0 and data.final_by == 2 else "Buyer" if data.accepted_by_id is not None and data.accepted_by_id > 0 and data.final_by == 1 else ""
                all_data['last_offer_by'] = last_offer.user_id if last_offer is not None else ""
                if obj.sale_by_type_id == 4:
                    offer_data = NegotiatedOffers.objects.filter(master_offer=data.id, status=1, offer_by=1).last()
                elif obj.sale_by_type_id == 7:
                    last_offer = HighestBestNegotiatedOffers.objects.filter(master_offer=data.id, status=1).last()
                    if last_offer is not None and last_offer.offer_by == 2 and last_offer.best_offer_is_accept == 1:
                        offer_data = last_offer
                    else:
                        offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer=data.id, offer_by=1, status=1).last()
                all_data['offer_price'] = offer_data.offer_price if offer_data is not None else ""
                all_data['negotiation_id'] = data.id
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_current_best_offer(obj):
        try:
            if obj.sale_by_type_id == 4:
                offer_data = NegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, master_offer__is_declined=0, status=1).order_by("offer_price").last()
            else:
                offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, master_offer__is_declined=0, status=1, is_declined=0).order_by("offer_price").last()
            return offer_data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_offer_approved(obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, master_offer__is_declined=0, status=1, is_declined=0).count()
            return True if offer_data > 0 else False
        except Exception as exp:
            return False

    def get_your_approved_best_offer(self, obj):
        try:
            # offer_data = HighestBestNegotiatedOffers.objects.filter(user=self.context, master_offer__property=obj.id, best_offer_is_accept=1, master_offer__is_declined=0, status=1, is_declined=0).last()
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__user=self.context, master_offer__property=obj.id, best_offer_is_accept=1, master_offer__is_declined=0, status=1, is_declined=0).last()
            return offer_data.offer_price
        except Exception as exp:
            return 0

    def get_is_your_best_offer_accepted(self, obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(user=self.context, master_offer__property=obj.id, master_offer__is_declined=0, status=1, is_declined=0).last()
            return True if offer_data is not None and offer_data.best_offer_is_accept == 1 else False
        except Exception as exp:
            return False

    def get_is_last_best_offer_accepted(self, obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__user=self.context, master_offer__property=obj.id, master_offer__is_declined=0, status=1, is_declined=0).last()
            return True if offer_data is not None and offer_data.best_offer_is_accept == 1 else False
        except Exception as exp:
            return False

    @staticmethod
    def get_inline_step(obj):
        try:
            if obj.sale_by_type_id == 2:
                data = obj.insider_auction_step_winner_property.filter(status=1).last()
                if data is None:
                    return 1
                elif data is not None and int(data.insider_auction_step) == 1:
                    return 2
                elif data is not None and int(data.insider_auction_step) == 2:
                    return 3
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).last().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_dutch_winning_user(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=1, status=1).last().user_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_seal_winning_amount(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).last().amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_seal_winning_user(obj):
        try:
            return obj.insider_auction_step_winner_property.filter(insider_auction_step=2, status=1).last().user_id
        except Exception as exp:
            return ""

    def get_your_seal_amount(self, obj):
        try:
            return obj.bid_property.filter(user=int(self.context), insider_auction_step=2, auction_type=2, is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_total_bid_till_sealed(obj):
        try:
            return obj.bid_property.filter(insider_auction_step__in=[1, 2], auction_type=2, is_canceled=0).count()
        except Exception as exp:
            return ""

    def get_sealed_user_bid_count(self, obj):
        try:
            return obj.bid_property.filter(user=self.context, insider_auction_step__in=[2], auction_type=2, is_canceled=0).count()
        except Exception as exp:
            return ""

    def get_english_user_bid_count(self, obj):
        try:
            return obj.bid_property.filter(user=self.context, insider_auction_step__in=[3], auction_type=2, is_canceled=0).count()
        except Exception as exp:
            return ""

    def get_user_current_sealed_bid(self, obj):
        try:
            data = ""
            sealed_bid = obj.bid_property.filter(user=self.context, insider_auction_step__in=[2], auction_type=2, is_canceled=0).last()
            if sealed_bid is None:
                sealed_bid = obj.insider_auction_step_winner_property.filter(insider_auction_step=1).first()
                data = sealed_bid.amount
            else:
                data = sealed_bid.bid_amount
            return data
        except Exception as exp:
            return ""

    def get_registration_id(self, obj):
        try:
            data = obj.bid_registration_property.filter(domain=obj.domain_id, user=self.context, status=1).last()
            if data is not None:
                return data.id
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_idx_property_image(obj):
        try:
            if obj.idx_property_id:
                return obj.property_idx_property_uploads.filter(status=1).values('id', 'upload')
            else:
                return []
        except Exception as exp:
            return []

    @staticmethod
    def get_buyer_premium_text(obj):
        try:
            if obj.buyers_premium:
                text = ""
                if obj.buyers_premium_min_amount is not None and obj.buyers_premium_min_amount > 0:
                    text += 'Buyers Premium $' + str(obj.buyers_premium_min_amount)
                if obj.buyers_premium_percentage is not None and obj.buyers_premium_percentage > 0:
                    if text == "":
                        text += 'Buyers Premium ' + str(obj.buyers_premium_percentage) + ' %'
                    else:
                        text += ' or ' + str(obj.buyers_premium_percentage) + ' %'
                return text
            else:
                return None
        except Exception as exp:
            return None
        
    @staticmethod
    def get_new_today(obj):
        try:
            if obj.added_on.date() == timezone.now().date(): 
                return True
            else:
                return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_is_deposit_required(obj):
        try:
            users = Users.objects.filter(site=obj.domain_id, status=1).last()
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0,
                                                   status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0,
                                                       is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                           is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                       is_agent=0, status=1, is_deposit_required=1).last()

            if data is not None:
                return data.is_deposit_required
            else:
                return 0
        except Exception as exp:
            return 0

    @staticmethod
    def get_deposit_amount(obj):
        try:
            users = Users.objects.filter(site=obj.domain_id, status=1).last()
            data = PropertySettings.objects.filter(domain=obj.domain_id, property=obj.id, is_broker=0, is_agent=0,
                                                   status=1, is_deposit_required=1).last()
            if data is None and obj.agent_id != users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=0,
                                                       is_agent=1, status=1, is_deposit_required=1).last()
                if data is None:
                    data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                           is_agent=0, status=1, is_deposit_required=1).last()
            elif data is None and obj.agent_id == users.id:
                data = PropertySettings.objects.filter(domain=obj.domain_id, property__isnull=True, is_broker=1,
                                                       is_agent=0, status=1, is_deposit_required=1).last()

            if data is not None and data.is_deposit_required:
                return int(data.deposit_amount)
            else:
                return ""
        except Exception as exp:
            return ""        


class PropertyAdvertisementSerializer(serializers.ModelSerializer):
    """
    PropertyAdvertisementSerializer
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = Advertisement
        fields = ("id", "company_name", "url", "image")

    @staticmethod
    def get_image(obj):
        try:
            data = {
                "doc_file_name": obj.image.doc_file_name,
                "bucket_name": obj.image.bucket_name
            }
            return data
        except Exception as exp:
            return {}


class PropertySettingSerializer(serializers.ModelSerializer):
    """
    PropertySettingSerializer
    """
    auction_id = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()

    class Meta:
        model = PropertySettings
        #fields = "__all__"
        fields = ("id", "domain", "property", "user", "is_broker", "is_agent", "auto_approval", "bid_limit", "show_reverse_not_met", "is_log_time_extension", "time_flash", "log_time_extension", "remain_time_to_add_extension", "status", "added_on", "updated_on", "auction_id",
                   "is_deposit_required", "deposit_amount")

    @staticmethod
    def get_auction_id(obj):
        try:
            property_auction = PropertyAuction.objects.filter(property_id=obj.property_id).first()
            return property_auction.id
        except Exception as exp:
            return ""
        
    @staticmethod
    def get_deposit_amount(obj):
        try:
            if obj.is_deposit_required:
                return int(obj.deposit_amount)
            else:
                return 0
        except Exception as exp:
            return 0    


class FavouritePropertySerializer(serializers.ModelSerializer):
    """
    FavouritePropertySerializer
    """

    class Meta:
        model = FavouriteProperty
        fields = "__all__"



class SavePropertySettingSerializer(serializers.ModelSerializer):
    """
    SavePropertySettingSerializer
    """

    class Meta:
        model = PropertySettings
        fields = "__all__"

        
class WatchPropertySerializer(serializers.ModelSerializer):
    """
    WatchPropertySerializer
    """

    class Meta:
        model = WatchProperty
        fields = "__all__"


class FavouritePropertyListingSerializer(serializers.ModelSerializer):
    """
    FavouritePropertyListingSerializer
    """
    address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    city = serializers.CharField(source="property.city", read_only=True, default="")
    state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    auction_type = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="property.property_asset.name", read_only=True, default="")
    bid_increment = serializers.SerializerMethodField()
    auction_type_id = serializers.IntegerField(source="property.sale_by_type.id", read_only=True, default="0")
    current_best_offer_amount = serializers.SerializerMethodField()
    highest_best_format = serializers.IntegerField(source="property.highest_best_format", read_only=True, default="0")
    un_priced = serializers.SerializerMethodField()

    class Meta:
        model = FavouriteProperty
        fields = ("id", "address_one", "city", "state", "auction_type", "price", "added_on", "image", "property",
                  "property_type", "bid_increment", "postal_code", "auction_type_id", "current_best_offer_amount",
                  "highest_best_format", "un_priced")

    @staticmethod
    def get_price(obj):
        try:
            data = obj.property.property_auction.first()
            # return data.offer_amount if data.auction_id == 7 else data.start_price
            return data.start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bid_increment(obj):
        try:
            data = obj.property.property_auction.first()
            return data.bid_increments if data.bid_increments is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_best_offer_amount(obj):
        try:
            if obj.property.sale_by_type_id == 7:
                return HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.property_id, is_declined=0, master_offer__is_declined=0, best_offer_is_accept=1).last().offer_price
            else:
                return ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_un_priced(obj):
        try:
            data = obj.property.property_auction.first()
            return data.un_priced
        except Exception as exp:
            return ""


class ScheduleTourSerializer(serializers.ModelSerializer):
    """
    ScheduleTourSerializer
    """

    class Meta:
        model = ScheduleTour
        fields = "__all__"


class ScheduleTourDetailSerializer(serializers.ModelSerializer):
    """
    ScheduleTourDetailSerializer
    """

    class Meta:
        model = Users
        fields = ("id", "first_name", "last_name", "email", "phone_no")


class SuperAdminScheduleTourSerializer(serializers.ModelSerializer):
    """
    SuperAdminScheduleTourSerializer
    """

    domain = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    domain_url =  serializers.SerializerMethodField()
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    # first_name = serializers.CharField(source="first_name", read_only=True, default="")
    # last_name = serializers.CharField(source="last_name", read_only=True, default="")
    # email = serializers.CharField(source="email", read_only=True, default="")
    # phone_no = serializers.CharField(source="phone_no", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    tour_type = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleTour
        fields = ("id", "domain", "property_address_one", "property_city", "property_state", "property_postal_code",
                  "first_name", "last_name", "email", "phone_no", "schedule_date", "message", "status", "property_id",
                  "tour_type", "availability", "domain_url")
    
    @staticmethod
    def get_domain_url(obj):
        try:
            subdomain_url = settings.SUBDOMAIN_URL
            raw_domain_url = subdomain_url.replace("###", obj.domain.domain_name)
            return raw_domain_url
        except:
            return ''

    @staticmethod
    def get_tour_type(obj):
        try:
            tour_type = {1: "In Person", 2: "Video Chat"}
            return tour_type[obj.tour_type]
        except Exception as exp:
            return ""

    @staticmethod
    def get_availability(obj):
        try:
            availability = {1: "Morning", 2: "Afternoon", 3: "Evening", 4: "Flexible"}
            return availability[obj.availability]
        except Exception as exp:
            return ""


class SubdomainScheduleTourSerializer(serializers.ModelSerializer):
    """
    SubdomainScheduleTourSerializer
    """
    domain = serializers.CharField(source="domain.domain_name", read_only=True, default="")
    property_address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    property_city = serializers.CharField(source="property.city", read_only=True, default="")
    property_state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    property_postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    # first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    # last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    # email = serializers.CharField(source="user.email", read_only=True, default="")
    # phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    tour_type = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleTour
        fields = ("id", "domain", "property_address_one", "property_city", "property_state", "property_postal_code",
                  "first_name", "last_name", "email", "phone_no", "schedule_date", "message", "status", "property_id",
                  "tour_type", "availability", "added_on")

    @staticmethod
    def get_tour_type(obj):
        try:
            tour_type = {1: "In Person", 2: "Video Chat"}
            return tour_type[obj.tour_type]
        except Exception as exp:
            return ""

    @staticmethod
    def get_availability(obj):
        try:
            availability = {1: "Morning", 2: "Afternoon", 3: "Evening", 4: "Flexible"}
            return availability[obj.availability]
        except Exception as exp:
            return ""


class DocumentVaultVisitSerializer(serializers.ModelSerializer):
    """
    DocumentVaultVisitSerializer
    """

    class Meta:
        model = DocumentVaultVisit
        fields = "__all__"


class SuperAdminFavouritePropertyListingSerializer(serializers.ModelSerializer):
    """
    SuperAdminFavouritePropertyListingSerializer
    """
    address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    city = serializers.CharField(source="property.city", read_only=True, default="")
    state = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    auction_type = serializers.CharField(source="property.sale_by_type.auction_type", read_only=True, default="")
    price = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="property.property_asset.name", read_only=True, default="")
    bid_increment = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()

    class Meta:
        model = FavouriteProperty
        fields = ("id", "address_one", "city", "state", "auction_type", "price", "added_on", "image", "property",
                  "property_type", "bid_increment", "postal_code", "user_detail")

    @staticmethod
    def get_price(obj):
        try:
            data = obj.property.property_auction.first()
            return data.offer_amount if data.auction_id == 7 else data.start_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bid_increment(obj):
        try:
            data = obj.property.property_auction.first()
            return data.bid_increments if data.bid_increments is not None else ""
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_detail(obj):
        try:
            data = {}
            data['id'] = obj.user_id
            data['first_name'] = obj.user.first_name
            data['last_name'] = obj.user.last_name
            data['email'] = obj.user.email
            data['domain_name'] = obj.domain.domain_name
            data['domain_url'] = obj.domain.domain_url
            return data
        except Exception as exp:
            return {}


class PropertyAuctionDashboardSerializer(serializers.ModelSerializer):
    """
    PropertyAuctionDashboardSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    status = serializers.CharField(source="status.status_name", read_only=True, default="")
    property_owner = serializers.SerializerMethodField()
    auction_data = serializers.SerializerMethodField()
    current_bid = serializers.SerializerMethodField()
    high_bidder = serializers.SerializerMethodField()
    next_bid = serializers.SerializerMethodField()
    total_bids = serializers.SerializerMethodField()
    bidder = serializers.SerializerMethodField()
    watcher = serializers.SerializerMethodField()
    reserve_price = serializers.SerializerMethodField()
    reserve_met = serializers.SerializerMethodField()
    high_bidder = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "status", "auction_data",
                  "current_bid", "high_bidder", "next_bid", "total_bids", "bidder", "watcher", "reserve_price",
                  "reserve_met", "property_owner", "read_by_auction_dashboard", "status_id", "domain", "domain_url")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_owner(obj):
        try:
            all_data = {}
            all_data['first_name'] = obj.agent.first_name
            all_data['last_name'] = obj.agent.last_name
            all_data['company'] = obj.domain.domain_name
            all_data['phone_no'] = obj.agent.phone_no
            all_data['email'] = obj.agent.email
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_auction_data(obj):
        try:
            auction = obj.property_auction.first()
            all_data = {
                "id": auction.id,
                "start_date": auction.start_date,
                "end_date": auction.end_date,
                "bid_increments": auction.bid_increments,
                "status": auction.status_id
            }
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_current_bid(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).last().bid_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_high_bidder(obj):
        try:
            all_data = {}
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                high_bidder_id = bidder.user_id
                bidder_detail = BidRegistrationAddress.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, address_type__in=[2, 3], status=1).last()
                all_data['first_name'] = bidder_detail.first_name
                all_data['last_name'] = bidder_detail.last_name
                all_data['registration_id'] = bidder_detail.registration.registration_id
                all_data['email'] = bidder_detail.email
                all_data['address_first'] = bidder_detail.address_first
                all_data['city'] = bidder_detail.city
                all_data['state'] = bidder_detail.state.state_name
                all_data['phone_no'] = bidder_detail.phone_no
                all_data['postal_code'] = bidder_detail.postal_code
                all_data['ip_address'] = bidder_detail.registration.ip_address
                all_data['bid_amount'] = bidder.bid_amount
                all_data['user_id'] = bidder.user_id
                # bid_limit = BidLimit.objects.filter(registration__user_id=high_bidder_id, registration__property_id=obj.id, is_approved=2, status=1).last()
                # all_data['approval_limit'] = bid_limit.approval_limit
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_next_bid(obj):
        try:
            bidder = obj.bid_property.filter(is_canceled=0)
            if bidder.count() > 0:
                bidder = bidder.last()
                return int(bidder.bid_amount) + int(bidder.auction.start_price)
            else:
                return obj.property_auction.first().start_price
        except Exception as exp:
            print(exp)
            return ""

    @staticmethod
    def get_total_bids(obj):
        try:
            return obj.bid_property.filter(is_canceled=0).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidder(obj):
        try:
            return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_watcher(obj):
        try:
            return obj.property_watcher_property.filter(property=obj.id).count()
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_price(obj):
        try:
            return obj.property_auction.first().reserve_amount
        except Exception as exp:
            return ""

    @staticmethod
    def get_reserve_met(obj):
        try:
            reserve_amount = obj.property_auction.first().reserve_amount
            max_bid_amount = obj.bid_property.filter(is_canceled=0).last().bid_amount
            if max_bid_amount >= reserve_amount:
                return "YES"
            else:
                return "NO"
        except Exception as exp:
            return "NO"


class AddPropertyEvaluatorQuestionSerializer(serializers.ModelSerializer):
    """
    AddPropertyEvaluatorQuestionSerializer
    """

    class Meta:
        model = PropertyEvaluatorQuestion
        fields = "__all__"


class PropertyEvaluatorQuestionDetailSerializer(serializers.ModelSerializer):
    """
    PropertyEvaluatorQuestionDetailSerializer
    """
    question_option = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorQuestion
        fields = ("id", "category", "question", "option_type", "status", "question_option", "property_type", "placeholder")

    @staticmethod
    def get_question_option(obj):
        try:
            return obj.property_evaluator_question_option.filter(status=1).values('id', "option")
        except Exception as exp:
            return ""


class PropertyEvaluatorQuestionSerializer(serializers.ModelSerializer):
    """
    PropertyEvaluatorQuestionSerializer
    """
    question_option = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorQuestion
        fields = ("id", "category", "question", "option_type", "status", "question_option", "property_type", "answer",
                  "placeholder", "documents")

    @staticmethod
    def get_question_option(obj):
        try:
            return obj.property_evaluator_question_option.filter(status=1).order_by("-id").values('id', "option")
        except Exception as exp:
            return ""

    def get_answer(self, obj):
        try:
            if obj.option_type != 4:
                return obj.property_evaluator_user_answer.filter(property_evaluator__domain_id=self.context['domain_id'], property_evaluator__user=self.context['user_id']).values('id', "answer")
            else:
                return obj.property_evaluator_user_answer.annotate(total_doc=Count("property_evaluator_doc_answer__id")).filter(property_evaluator__domain_id=self.context['domain_id'], property_evaluator__user=self.context['user_id']).values('id', "answer", "total_doc")
        except Exception as exp:
            return []

    def get_documents(self, obj):
        try:
            data = {}
            if obj.option_type == 4:
                answer = obj.property_evaluator_user_answer.filter(property_evaluator__user=self.context['user_id'], property_evaluator__domain=self.context['domain_id']).first()
                # if answer is not None and answer.answer is not None:
                #     uploads = UserUploads.objects.filter(id=int(answer.answer)).first()
                #     data['id'] = uploads.id
                #     data['doc_file_name'] = uploads.doc_file_name
                #     data['bucket_name'] = uploads.bucket_name
                data = UserUploads.objects.filter(property_evaluator_doc_answer_document__answer=answer.id).values('id', 'doc_file_name', 'bucket_name', bot_doc_id=F('property_evaluator_doc_answer_document__id'))
            return data
        except Exception as exp:
            return []


class SubdomainPropertyEvaluatorSerializer(serializers.ModelSerializer):
    """
    SubdomainPropertyEvaluatorSerializer
    """
    user_first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    user_last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    user_email = serializers.CharField(source="user.email", read_only=True, default="")
    user_phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    property_type = serializers.SerializerMethodField()
    complete_status = serializers.CharField(source="complete_status.status_name", read_only=True, default="")
    assign_to_first_name = serializers.CharField(source="assign_to.first_name", read_only=True, default="")
    assign_to_last_name = serializers.CharField(source="assign_to.last_name", read_only=True, default="")
    complete_status_id = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorDomain
        fields = ("id", "user_first_name", "user_last_name", "user_email", "user_phone_no", "added_on", "property_type",
                  "assign_to", "complete_status", "review_msg", "assign_to_first_name", "assign_to_last_name",
                  "complete_status_id", "user_type")

    @staticmethod
    def get_property_type(obj):
        try:
            data = obj.property_evaluator_user_answer_property_evaluator.filter(question=3).first()
            property_type = ""
            if int(data.answer) == 24:
                property_type = "Residential"
            elif int(data.answer) == 25:
                property_type = "Commercial"
            else:
                property_type = "Land"
            return property_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_complete_status_id(obj):
        try:
            return obj.complete_status_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            data = None
            if obj.user.user_type_id == 1:
                data = "Buyer"
            elif obj.user.site_id is not None and obj.user.user_type_id == 2:
                data = "Broker"
            else:
                data = "Agent"
            return data
        except Exception as exp:
            return ""


class AgentPropertyEvaluatorSerializer(serializers.ModelSerializer):
    """
    AgentPropertyEvaluatorSerializer
    """
    user_first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    user_last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    user_email = serializers.CharField(source="user.email", read_only=True, default="")
    user_phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    property_type = serializers.SerializerMethodField()
    complete_status = serializers.CharField(source="complete_status.status_name", read_only=True, default="")

    class Meta:
        model = PropertyEvaluatorDomain
        fields = ("id", "user_first_name", "user_last_name", "user_email", "user_phone_no", "added_on", "property_type",
                  "assign_to", "complete_status", "review_msg")

    @staticmethod
    def get_property_type(obj):
        try:
            data = obj.property_evaluator_user_answer_property_evaluator.filter(question=3).first()
            property_type = ""
            if int(data.answer) == 24:
                property_type = "Residential"
            elif int(data.answer) == 25:
                property_type = "Commercial"
            else:
                property_type = "Land"
            return property_type
        except Exception as exp:
            return ""


class PropertyEvaluatorDetailSerializer(serializers.ModelSerializer):
    """
    PropertyEvaluatorDetailSerializer
    """
    category = serializers.CharField(source="question.category_id", read_only=True, default="")
    question = serializers.CharField(source="question.question", read_only=True, default="")
    option_type = serializers.IntegerField(source="question.option_type", read_only=True, default="")
    question_option = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="question.property_type_id", read_only=True, default="")
    documents = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    user_detail = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorUserAnswer
        fields = ("id", "category", "question", "option_type", "question_option", "property_type", "answer", "documents", "user_detail")

    @staticmethod
    def get_question_option(obj):
        try:
            return obj.question.property_evaluator_question_option.filter(status=1).values('id', "option")
        except Exception as exp:
            return ""

    # def get_answer(self, obj):
    #     try:
    #         return obj.property_evaluator_user_answer.filter(property_evaluator__user=self.context).values('id', "answer")
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_documents(obj):
        try:
            data = {}
            if obj.question.option_type == 4:
                data = UserUploads.objects.filter(property_evaluator_doc_answer_document__answer=obj.id).values('id', 'doc_file_name', 'bucket_name', bot_doc_id=F('property_evaluator_doc_answer_document__id'))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_answer(obj):
        try:
            total_doc = PropertyEvaluatorDocAnswer.objects.filter(answer=obj.id).count()
            data = {"id": obj.id, "answer": obj.answer, "total_doc": total_doc}
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_user_detail(obj):
        try:
            profile_image = None
            if obj.property_evaluator.user.profile_image:
                profile_upload = UserUploads.objects.filter(id=int(obj.property_evaluator.user.profile_image)).first()
                profile_image = profile_upload.bucket_name+"/"+profile_upload.doc_file_name
            data = {"first_name": obj.property_evaluator.user.first_name, "last_name": obj.property_evaluator.user.last_name, "profile_image": profile_image}
            return data
        except Exception as exp:
            return {}


class RebaPropertyListingSerializer(serializers.ModelSerializer):
    """
    RebaPropertyListingSerializer
    """
    name = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    property_price = serializers.SerializerMethodField()
    state_name = serializers.CharField(source="state.state_name", read_only=True, default="")
    property_asset = serializers.CharField(source="property_asset.name", read_only=True, default="")
    is_favourite = serializers.SerializerMethodField()
    bidder_offer_count = serializers.SerializerMethodField()
    iso_state_name = serializers.CharField(source="state.iso_name", read_only=True, default="")
    status_id = serializers.IntegerField(source="status.id", read_only=True, default="")
    closing_status_name = serializers.CharField(source="closing_status.status_name", read_only=True, default="")
    property_current_price = serializers.SerializerMethodField()
    un_priced = serializers.SerializerMethodField()
    current_best_offer = serializers.SerializerMethodField()
    company_data = serializers.SerializerMethodField()
    domain_url = serializers.CharField(source="domain.domain_url", read_only=True, default="")

    class Meta:
        model = PropertyListing
        fields = ("id", "name", "auction_type", "bidding_start", "bidding_end", "status", "property_image",
                  "property_price", "is_featured", "city", "state_name", "postal_code", "property_asset",
                  "sale_by_type", "address_one", "is_favourite", "bidder_offer_count", "iso_state_name", "added_on",
                  "status_id", "closing_status", "closing_status_name", "property_current_price", "un_priced",
                  "due_diligence_period", "escrow_period", "earnest_deposit", "earnest_deposit_type",
                  "current_best_offer", "highest_best_format", "company_data", "domain_url")

    @staticmethod
    def get_name(obj):
        try:
            name = obj.address_one
            name += ", "+obj.city if obj.city is not None else ""
            name += ", " + obj.state.state_name if obj.state is not None else ""
            name += " " + obj.postal_code if obj.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_location(obj):
        try:
            name = obj.city
            name += ", " + obj.state.state_name if obj.state is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_price(obj):
        try:
            return obj.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_is_favourite(self, obj):
        try:
            user_id = self.context['user_id']
            if user_id is not None:
                data = obj.property_favourite_property.filter(domain=obj.domain_id, property=obj.id, user=user_id).first()
                if data is not None:
                    return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bidder_offer_count(obj):
        try:
            return obj.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_property_current_price(obj):
        try:
            bid = obj.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if obj.sale_by_type_id not in [4, 7] and bid is not None:
                return bid.bid_amount
            else:
                return 0
        except Exception as exp:
            return ""

    @staticmethod
    def get_un_priced(obj):
        try:
            return obj.property_auction.first().un_priced
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_best_offer(obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.id, best_offer_is_accept=1, status=1).order_by("offer_price").last()
            return offer_data.offer_price
        except Exception as exp:
            return ""

    @staticmethod
    def get_company_data(obj):
        try:
            data = {}
            company_data = UserBusinessProfile.objects.filter(user__site=obj.domain_id, status=1).first()
            data['company_name'] = company_data.company_name
            data['company_logo'] = {}
            if company_data.company_logo:
                logo_data = UserUploads.objects.filter(id=company_data.company_logo).first()
                if logo_data is not None:
                    logo = {"id": logo_data.id, "doc_file_name": logo_data.doc_file_name, "bucket_name": logo_data.bucket_name}
                    data['company_logo'] = logo
            return data
        except Exception as exp:
            return {}


class SuperAdminPropertyEvaluatorListSerializer(serializers.ModelSerializer):
    """
    SuperAdminPropertyEvaluatorListSerializer
    """
    user_first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    user_last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    user_email = serializers.CharField(source="user.email", read_only=True, default="")
    user_phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")
    property_type = serializers.SerializerMethodField()
    complete_status = serializers.CharField(source="complete_status.status_name", read_only=True, default="")
    assign_to_first_name = serializers.CharField(source="assign_to.first_name", read_only=True, default="")
    assign_to_last_name = serializers.CharField(source="assign_to.last_name", read_only=True, default="")
    complete_status_id = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    domain_name = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorDomain
        fields = ("id", "user_first_name", "user_last_name", "user_email", "user_phone_no", "added_on", "property_type",
                  "assign_to", "complete_status", "review_msg", "assign_to_first_name", "assign_to_last_name",
                  "complete_status_id", "user_type", "domain_name")

    @staticmethod
    def get_property_type(obj):
        try:
            data = obj.property_evaluator_user_answer_property_evaluator.filter(question=3).first()
            property_type = ""
            if int(data.answer) == 24:
                property_type = "Residential"
            elif int(data.answer) == 25:
                property_type = "Commercial"
            else:
                property_type = "Land"
            return property_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_complete_status_id(obj):
        try:
            return obj.complete_status_id
        except Exception as exp:
            return ""

    @staticmethod
    def get_user_type(obj):
        try:
            data = None
            if obj.user.user_type_id == 1:
                data = "Buyer"
            elif obj.user.site_id is not None and obj.user.user_type_id == 2:
                data = "Broker"
            else:
                data = "Agent"
            return data
        except Exception as exp:
            return ""

    @staticmethod
    def get_domain_name(obj):
        try:
            data = UserBusinessProfile.objects.filter(user__site=obj.domain_id).first()
            return data.company_name
        except Exception as exp:
            return ""


class SuperAdminPropertyEvaluatorDetailSerializer(serializers.ModelSerializer):
    """
    SuperAdminPropertyEvaluatorDetailSerializer
    """
    category = serializers.CharField(source="question.category_id", read_only=True, default="")
    question = serializers.CharField(source="question.question", read_only=True, default="")
    option_type = serializers.IntegerField(source="question.option_type", read_only=True, default="")
    question_option = serializers.SerializerMethodField()
    property_type = serializers.CharField(source="question.property_type_id", read_only=True, default="")
    documents = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()

    class Meta:
        model = PropertyEvaluatorUserAnswer
        fields = ("id", "category", "question", "option_type", "question_option", "property_type", "answer", "documents")

    @staticmethod
    def get_question_option(obj):
        try:
            return obj.question.property_evaluator_question_option.filter(status=1).values('id', "option")
        except Exception as exp:
            return ""

    # def get_answer(self, obj):
    #     try:
    #         return obj.property_evaluator_user_answer.filter(property_evaluator__user=self.context).values('id', "answer")
    #     except Exception as exp:
    #         return ""

    @staticmethod
    def get_documents(obj):
        try:
            data = {}
            if obj.question.option_type == 4:
                data = UserUploads.objects.filter(property_evaluator_doc_answer_document__answer=obj.id).values('id', 'doc_file_name', 'bucket_name', bot_doc_id=F('property_evaluator_doc_answer_document__id'))
            return data
        except Exception as exp:
            return []

    @staticmethod
    def get_answer(obj):
        try:
            total_doc = PropertyEvaluatorDocAnswer.objects.filter(answer=obj.id).count()
            data = {"id": obj.id, "answer": obj.answer, "total_doc": total_doc}
            return data
        except Exception as exp:
            return {}


class AddPortfolioSerializer(serializers.ModelSerializer):
    """
    AddPortfolioSerializer
    """

    class Meta:
        model = Portfolio
        fields = "__all__"


class PortfolioListingSerializer(serializers.ModelSerializer):
    """
    PortfolioListingSerializer
    """
    user = serializers.SerializerMethodField()
    no_property = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "user", "name", "details", "terms", "contact", "added_on", "no_property")

    @staticmethod
    def get_user(obj):
        try:
            data = {}
            data['first_name'] = obj.user.first_name
            data['last_name'] = obj.user.last_name
            data['email'] = obj.user.email
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_no_property(obj):
        try:
            return obj.property_portfolio.count()
        except Exception as exp:
            return 0


class AdminPortfolioListingSerializer(serializers.ModelSerializer):
    """
    AdminPortfolioListingSerializer
    """
    user = serializers.SerializerMethodField()
    no_property = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "user", "name", "details", "terms", "contact", "added_on", "no_property")

    @staticmethod
    def get_user(obj):
        try:
            data = {}
            data['first_name'] = obj.user.first_name
            data['last_name'] = obj.user.last_name
            data['email'] = obj.user.email
            return data
        except Exception as exp:
            return {}

    @staticmethod
    def get_no_property(obj):
        try:
            return obj.property_portfolio.count()
        except Exception as exp:
            return 0


class PortfolioDetailSerializer(serializers.ModelSerializer):
    """
    PortfolioDetailSerializer
    """
    property = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "name", "details", "terms", "contact", "status", "property", "images")

    @staticmethod
    def get_property(obj):
        try:
            return obj.property_portfolio.values('id', "property")
        except Exception as exp:
            return []

    @staticmethod
    def get_images(obj):
        try:
            return obj.property_portfolio_images.values('id', doc_id=F("upload__id"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class AdminPortfolioDetailSerializer(serializers.ModelSerializer):
    """
    AdminPortfolioDetailSerializer
    """
    property = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "name", "details", "terms", "contact", "status", "property", "images")

    @staticmethod
    def get_property(obj):
        try:
            return obj.property_portfolio.values('id', "property")
        except Exception as exp:
            return []

    @staticmethod
    def get_images(obj):
        try:
            return obj.property_portfolio_images.values('id', doc_id=F("upload__id"), doc_file_name=F("upload__doc_file_name"), bucket_name=F("upload__bucket_name"))
        except Exception as exp:
            return []


class ViewCountPropertyDetailSerializer(serializers.ModelSerializer):
    """
    ViewCountPropertyDetailSerializer
    """
    property_image = serializers.SerializerMethodField()
    state = serializers.CharField(source="state.state_name", read_only=True, default="")
    auction_type = serializers.CharField(source="sale_by_type.auction_type", read_only=True, default="")
    bid_increment = serializers.SerializerMethodField()

    class Meta:
        model = PropertyListing
        fields = ("id", "property_image", "address_one", "city", "state", "postal_code", "auction_type", "bid_increment")

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_bid_increment(obj):
        try:
            return obj.property_auction.first().bid_increments
        except Exception as exp:
            return ""


class PropertyVewCountDetailSerializer(serializers.ModelSerializer):
    """
    PropertyVewCountDetailSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")

    class Meta:
        model = PropertyView
        fields = ("id", "first_name", "last_name", "email", "phone_no", "added_on")


class PropertyWatcherCountDetailSerializer(serializers.ModelSerializer):
    """
    PropertyWatcherCountDetailSerializer
    """
    first_name = serializers.CharField(source="user.first_name", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")

    class Meta:
        model = PropertyWatcher
        fields = ("id", "first_name", "last_name", "email", "phone_no", "added_on")


class ParcelDetailSerializer(serializers.ModelSerializer):
    """
    ParcelDetailSerializer
    """
    name = serializers.SerializerMethodField()
    auction_type = serializers.SerializerMethodField()
    bidding_start = serializers.SerializerMethodField()
    bidding_end = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    property_image = serializers.SerializerMethodField()
    property_price = serializers.SerializerMethodField()
    is_featured = serializers.IntegerField(source="property.is_featured", read_only=True, default="")
    city = serializers.CharField(source="property.city", read_only=True, default="")
    state_name = serializers.CharField(source="property.state.state_name", read_only=True, default="")
    postal_code = serializers.CharField(source="property.postal_code", read_only=True, default="")
    property_asset = serializers.CharField(source="property.property_asset.name", read_only=True, default="")
    sale_by_type = serializers.CharField(source="property.sale_by_type_id", read_only=True, default="")
    address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    is_favourite = serializers.SerializerMethodField()
    bidder_offer_count = serializers.SerializerMethodField()
    iso_state_name = serializers.CharField(source="property.state.iso_name", read_only=True, default="")
    status_id = serializers.CharField(source="property.status.id", read_only=True, default="")
    closing_status = serializers.CharField(source="property.closing_status_id", read_only=True, default="")
    closing_status_name = serializers.CharField(source="closing_status.status_name", read_only=True, default="")
    property_current_price = serializers.SerializerMethodField()
    un_priced = serializers.SerializerMethodField()
    current_best_offer = serializers.SerializerMethodField()
    registration_id = serializers.SerializerMethodField()
    registration_approval = serializers.SerializerMethodField()

    class Meta:
        model = PropertyPortfolio
        fields = ("id", "name", "auction_type", "bidding_start", "bidding_end", "status", "property_image",
                  "property_price", "is_featured", "city", "state_name", "postal_code", "property_asset",
                  "sale_by_type", "address_one", "is_favourite", "bidder_offer_count", "iso_state_name",
                  "status_id", "closing_status", "closing_status_name", "property_current_price", "un_priced",
                  "current_best_offer", "property_id", "registration_id", "registration_approval")

    @staticmethod
    def get_name(obj):
        try:
            name = obj.property.address_one
            name += ", "+obj.property.city if obj.property.city is not None else ""
            name += ", " + obj.property.state.state_name if obj.property.state is not None else ""
            name += " " + obj.property.postal_code if obj.property.postal_code is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_auction_type(obj):
        try:
            return obj.property.sale_by_type.auction_type
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_start(obj):
        try:
            return obj.property.property_auction.first().start_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_bidding_end(obj):
        try:
            return obj.property.property_auction.first().end_date
        except Exception as exp:
            return ""

    @staticmethod
    def get_status(obj):
        try:
            return obj.property.status.status_name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_location(obj):
        try:
            name = obj.property.city
            name += ", " + obj.property.state.state_name if obj.property.state is not None else ""
            return name
        except Exception as exp:
            return ""

    @staticmethod
    def get_property_image(obj):
        try:
            data = obj.property.property_uploads_property.filter(upload_type=1).first()
            all_data = {"image": data.upload.doc_file_name, "bucket_name": data.upload.bucket_name}
            return all_data
        except Exception as exp:
            return {}

    @staticmethod
    def get_property_price(obj):
        try:
            return obj.property.property_auction.first().start_price
        except Exception as exp:
            return ""

    def get_is_favourite(self, obj):
        try:
            user_id = self.context['user_id']
            if user_id is not None:
                data = obj.property.property_favourite_property.filter(domain=obj.portfolio.domain_id, property=obj.id, user=user_id).first()
                if data is not None:
                    return True
            return False
        except Exception as exp:
            return False

    @staticmethod
    def get_bidder_offer_count(obj):
        try:
            return obj.property.bid_registration_property.filter(status=1).count()
        except Exception as exp:
            return 0

    @staticmethod
    def get_property_current_price(obj):
        try:
            bid = obj.property.bid_property.filter(bid_type__in=[2, 3], is_canceled=0).last()
            if obj.sale_by_type_id not in [4, 7] and bid is not None:
                return bid.bid_amount
            else:
                return 0
        except Exception as exp:
            return ""

    @staticmethod
    def get_un_priced(obj):
        try:
            return obj.property.property_auction.first().un_priced
        except Exception as exp:
            return ""

    @staticmethod
    def get_current_best_offer(obj):
        try:
            offer_data = HighestBestNegotiatedOffers.objects.filter(master_offer__property=obj.property_id, best_offer_is_accept=1, status=1).order_by("offer_price").last()
            return offer_data.offer_price
        except Exception as exp:
            return ""

    def get_registration_id(self, obj):
        try:
            data = obj.property.bid_registration_property.filter(domain=obj.portfolio.domain_id, user=self.context, status=1).last()
            if data is not None:
                return data.id
            else:
                return ""
        except Exception as exp:
            return ""

    def get_registration_approval(self, obj):
        try:
            data = obj.property.bid_registration_property.filter(domain=obj.portfolio.domain_id, user=self.context, status=1).last()
            if data is not None:
                approval = {1: "Pending", 2: "Approved", 3: "Declined", 4: "Not Interested"}
                if data.is_approved == 2 and data.is_reviewed:
                    return "Registration Approved"
                elif data.is_approved == 3:
                    return "Registration Declined"
                else:
                    # return approval[int(obj.is_approved)]
                    return "Registration Pending Approval"
            else:
                return False
        except Exception as exp:
            return False


class ParcelDetailSerializerOld(serializers.ModelSerializer):
    """
    ParcelDetailSerializer
    """
    address_one = serializers.CharField(source="property.address_one", read_only=True, default="")
    address_two = serializers.CharField(source="property.address_two", read_only=True, default="")
    city = serializers.CharField(source="property.city", read_only=True, default="")
    state = serializers.CharField(source="property.city", read_only=True, default="")
    last_name = serializers.CharField(source="user.last_name", read_only=True, default="")
    email = serializers.CharField(source="user.email", read_only=True, default="")
    phone_no = serializers.CharField(source="user.phone_no", read_only=True, default="")

    class Meta:
        model = PropertyPortfolio
        fields = ("id", "first_name", "last_name", "email", "phone_no", "added_on")


class AddBulkPropertySerializer(serializers.ModelSerializer):
    """
    AddBulkPropertySerializer
    """

    class Meta:
        model = PropertyListing
        fields = "__all__"


class AddBulkAuctionSerializer(serializers.ModelSerializer):
    """
    AddBulkAuctionSerializer
    """

    class Meta:
        model = PropertyAuction
        fields = "__all__"