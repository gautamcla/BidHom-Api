# -*- coding: utf-8 -*-
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.viewsets import ViewSet
from api.packages.response import Response as response
from api.property.models import *
import datetime
from django.utils import timezone
from api.property.serializers import *
from api.packages.globalfunction import *
from django.db import transaction
from rest_framework.authentication import TokenAuthentication
from oauth2_provider.contrib.rest_framework import *
from django.db.models import F
from django.db.models import Q
from django.conf import settings
from django.db.models.functions import Concat
from django.db.models import Value as V
from datetime import timedelta
from django.db.models import CharField
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
from api.packages.mail_service import send_email, compose_email, send_custom_email
from api.packages.multiupload import *
from api.packages.common import *
import pandas as pd
from api.packages.constants import *
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class AddPropertyApiView(APIView):
    """
    Add/Update Property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            property_id = None
            check_update = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                check_update = True
                property_id = PropertyListing.objects.filter(id=property_id, domain=site_id).first()
                if property_id is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
            if "step" in data and data['step'] != "":
                step = int(data['step'])
            else:
                return Response(response.parsejson("step is required.", "", status=403))
            user_domain = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                if property_id is not None:
                    user_id = property_id.agent_id
                data["agent"] = user_id
                user_domain = users.site_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if step == 1:
                un_priced = 0
                if "un_priced" in data and data['un_priced'] != "":
                    un_priced = int(data['un_priced'])

                required_all = 0
                if "required_all" in data and data['required_all'] != "":
                    required_all = int(data['required_all'])

                if "property_asset" in data and data['property_asset'] != "":
                    property_asset = int(data['property_asset'])
                    asset = LookupPropertyAsset.objects.filter(id=property_asset, is_active=1).first()
                    if asset is None:
                        return Response(response.parsejson("Property asset not available.", "", status=403))
                else:
                    return Response(response.parsejson("property_asset is required.", "", status=403))

                if "address_one" in data and data['address_one'] != "":
                    address_one = data['address_one']
                else:
                    return Response(response.parsejson("address_one is required.", "", status=403))

                if "city" in data and data['city'] != "":
                    city = data['city']
                else:
                    return Response(response.parsejson("city is required.", "", status=403))

                if "state" in data and data['state'] != "":
                    state = int(data['state'])
                else:
                    return Response(response.parsejson("state is required.", "", status=403))

                if "postal_code" in data and data['postal_code'] != "":
                    postal_code = int(data['postal_code'])
                else:
                    return Response(response.parsejson("postal_code is required.", "", status=403))

                if "property_type" in data and data['property_type'] != "":
                    property_type = int(data['property_type'])
                else:
                    return Response(response.parsejson("property_type is required.", "", status=403))

                if "sale_by_type" in data and data['sale_by_type'] != "":
                    sale_by_type = int(data['sale_by_type'])
                else:
                    return Response(response.parsejson("sale_by_type is required.", "", status=403))

                if sale_by_type in [1, 7]:
                    if "buyers_premium" in data and data['buyers_premium'] != "":
                        buyers_premium = int(data['buyers_premium'])
                    else:
                        return Response(response.parsejson("buyers_premium is required.", "", status=403))
                    if buyers_premium:
                        if "buyers_premium_percentage" in data and data['buyers_premium_percentage'] != "" and float(data['buyers_premium_percentage']) > 0:
                            buyers_premium_percentage = data['buyers_premium_percentage']
                        else:
                            return Response(response.parsejson("buyers_premium_percentage is required.", "", status=403))

                        # if "buyers_premium_min_amount" in data and data['buyers_premium_min_amount'] != "" and float(data['buyers_premium_min_amount']) > 0:
                        #     buyers_premium_min_amount = data['buyers_premium_min_amount']
                        # else:
                        #     return Response(response.parsejson("buyers_premium_min_amount is required.", "", status=403))
                else:
                    data['buyers_premium'] = False
                    data['buyers_premium_percentage'] = None
                    data['buyers_premium_min_amount'] = None

                # -------------For Deposit Listings-------------
                if sale_by_type in [1, 2]:
                    data['deposit_amount'] = data['deposit_amount'] if int(data['is_deposit_required']) == 1 else 0 
                else:
                    data['deposit_amount'] = 0
                    data['is_deposit_required'] = 0

                if sale_by_type == 6:
                    if "auction_location" in data and data['auction_location'] != "":
                        auction_location = data['auction_location']
                    else:
                        return Response(response.parsejson("auction_location is required.", "", status=403))

                if sale_by_type == 7 and required_all == 1:
                    if "due_diligence_period" in data and data['due_diligence_period'] != "":
                        due_diligence_period = int(data['due_diligence_period'])
                    else:
                        return Response(response.parsejson("due_diligence_period is required.", "", status=403))

                    if "escrow_period" in data and data['escrow_period'] != "":
                        escrow_period = int(data['escrow_period'])
                    else:
                        return Response(response.parsejson("escrow_period is required.", "", status=403))

                    if "earnest_deposit" in data and data['earnest_deposit'] != "":
                        earnest_deposit = data['earnest_deposit']
                    else:
                        return Response(response.parsejson("earnest_deposit is required.", "", status=403))

                    if "earnest_deposit_type" in data and data['earnest_deposit_type'] != "":
                        earnest_deposit_type = int(data['earnest_deposit_type'])
                    else:
                        return Response(response.parsejson("earnest_deposit_type is required.", "", status=403))

                    if "highest_best_format" in data and data['highest_best_format'] != "":
                        highest_best_format = int(data['highest_best_format'])
                    else:
                        return Response(response.parsejson("highest_best_format is required.", "", status=403))

                if "status" in data and data['status'] != "":
                    status = int(data['status'])
                else:
                    data['status'] = 2

                if property_asset != 1:
                    if "property_opening_dates" in data and type(data['property_opening_dates']) == list and len(data['property_opening_dates']) > 0:
                        property_opening_dates = data['property_opening_dates']
                    else:
                        return Response(response.parsejson("property_opening_dates is required.", "", status=403))

                if "property_auction_data" in data and type(data["property_auction_data"]) == dict and len(data["property_auction_data"]) > 0:
                    property_auction_data = data["property_auction_data"]
                    if "auction_status" in property_auction_data and property_auction_data["auction_status"] != "":
                        auction_status = int(property_auction_data["auction_status"])
                    else:
                        return Response(response.parsejson("property_auction_data->auction_status is required.", "", status=403))

                    if sale_by_type == 7:
                        start_price = None
                        if required_all == 1:
                            if "start_price" in property_auction_data and property_auction_data['start_price'] != "":
                                start_price = property_auction_data['start_price']
                            else:
                                if not un_priced:
                                    return Response(response.parsejson("property_auction_data->start_price is required.", "", status=403))
                                # else:
                                #     start_price = None
                    else:
                        if "start_price" in property_auction_data and property_auction_data['start_price'] != "":
                            start_price = property_auction_data['start_price']
                        else:
                            return Response(response.parsejson("property_auction_data->start_price is required.", "", status=403))
                    if sale_by_type != 4:   # ----------- Not traditional auction
                        if "start_date" in property_auction_data and property_auction_data['start_date'] != "":
                            start_date = property_auction_data['start_date']
                        else:
                            return Response(response.parsejson("property_auction_data->start_date is required.", "", status=403))

                        if "end_date" in property_auction_data and property_auction_data['end_date'] != "":
                            end_date = property_auction_data['end_date']
                        else:
                            return Response(response.parsejson("property_auction_data->end_date is required.", "", status=403))
                    if sale_by_type == 1:
                        if "bid_increments" in property_auction_data and property_auction_data['bid_increments'] != "":
                            bid_increments = property_auction_data['bid_increments']
                        else:
                            return Response(response.parsejson("property_auction_data->bid_increments is required.", "", status=403))

                    # if sale_by_type != 2:
                    if sale_by_type != 2 and sale_by_type != 7:
                        if "reserve_amount" in property_auction_data and property_auction_data['reserve_amount'] != "" and property_auction_data['reserve_amount'] is not None:
                            reserve_amount = property_auction_data['reserve_amount']
                            if float(start_price) > float(reserve_amount):
                                return Response(response.parsejson("reserve_amount should be greater than start_price.", "", status=403))

                    if sale_by_type == 2:
                        if "bid_increments" in property_auction_data and property_auction_data['bid_increments'] != "":
                            bid_increments = property_auction_data['bid_increments']
                        else:
                            return Response(response.parsejson("property_auction_data->bid_increments is required.", "", status=403))

                        if "insider_price_decrease" in property_auction_data and property_auction_data['insider_price_decrease'] != "":
                            insider_price_decrease = property_auction_data['insider_price_decrease']
                        else:
                            return Response(response.parsejson("property_auction_data->insider_price_decrease is required.", "", status=403))

                        if "dutch_time" in property_auction_data and property_auction_data['dutch_time'] != "":
                            dutch_time = property_auction_data['dutch_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_time is required.", "", status=403))

                        if "start_date" in property_auction_data and property_auction_data['start_date'] != "":
                            start_date = property_auction_data['start_date']
                        else:
                            return Response(response.parsejson("property_auction_data->start_date is required.", "", status=403))

                        if "dutch_end_time" in property_auction_data and property_auction_data['dutch_end_time'] != "":
                            dutch_end_time = property_auction_data['dutch_end_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_end_time is required.", "", status=403))

                        if "dutch_pause_time" in property_auction_data and property_auction_data['dutch_pause_time'] != "":
                            dutch_pause_time = property_auction_data['dutch_pause_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_pause_time is required.", "", status=403))

                        if "sealed_time" in property_auction_data and property_auction_data['sealed_time'] != "":
                            sealed_time = property_auction_data['sealed_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_time is required.", "", status=403))

                        if "sealed_start_time" in property_auction_data and property_auction_data['sealed_start_time'] != "":
                            sealed_start_time = property_auction_data['sealed_start_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_start_time is required.", "", status=403))

                        if "sealed_end_time" in property_auction_data and property_auction_data['sealed_end_time'] != "":
                            sealed_end_time = property_auction_data['sealed_end_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_end_time is required.", "", status=403))

                        if "sealed_pause_time" in property_auction_data and property_auction_data['sealed_pause_time'] != "":
                            sealed_pause_time = property_auction_data['sealed_pause_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_pause_time is required.", "", status=403))

                        if "english_time" in property_auction_data and property_auction_data['english_time'] != "":
                            english_time = property_auction_data['english_time']
                        else:
                            return Response(response.parsejson("property_auction_data->english_time is required.", "", status=403))

                        if "english_start_time" in property_auction_data and property_auction_data['english_start_time'] != "":
                            english_start_time = property_auction_data['english_start_time']
                        else:
                            return Response(response.parsejson("property_auction_data->english_start_time is required.", "", status=403))

                        # if "english_end_time" in property_auction_data and property_auction_data['english_end_time'] != "":
                        #     english_end_time = property_auction_data['english_end_time']
                        # else:
                        #     return Response(response.parsejson("property_auction_data->english_end_time is required.", "", status=403))
                else:
                    return Response(response.parsejson("property_auction_data is required.", "", status=403))

                if property_asset == 3:
                    if "beds" in data and data['beds'] != "":
                        beds = int(data['beds'])
                    else:
                        return Response(response.parsejson("beds is required.", "", status=403))

                    if "baths" in data and data['baths'] != "":
                        baths = int(data['baths'])
                    else:
                        return Response(response.parsejson("baths is required.", "", status=403))

                    if "year_built" in data and data['year_built'] != "":
                        year_built = int(data['year_built'])
                    else:
                        return Response(response.parsejson("year_built is required.", "", status=403))

                    if "square_footage" in data and data['square_footage'] != "":
                        square_footage = int(data['square_footage'])
                    else:
                        return Response(response.parsejson("square_footage is required.", "", status=403))
                elif property_asset == 2:
                    if "year_built" in data and data['year_built'] != "":
                        year_built = int(data['year_built'])
                    else:
                        return Response(response.parsejson("year_built is required.", "", status=403))

                    if "square_footage" in data and data['square_footage'] != "":
                        square_footage = int(data['square_footage'])
                    else:
                        return Response(response.parsejson("square_footage is required.", "", status=403))
                data["create_step"] = 1
                # data["status"] = 1
                data["title"] = "testing"
                if user_domain == site_id:
                    data['is_approved'] = 1
                serializer = AddPropertySerializer(property_id, data=data)
                if serializer.is_valid():
                    property_id = serializer.save()
                    property_id = property_id.id
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                # ----------------------Property Auction---------------------
                if "property_auction_data" in data and type(data["property_auction_data"]) == dict and len(data["property_auction_data"]) > 0:
                    property_auction_data = data["property_auction_data"]
                    property_auction = PropertyAuction.objects.filter(property=property_id).first()
                    if property_auction is None:
                        property_auction = PropertyAuction()
                        property_auction.property_id = property_id
                    property_auction.start_date = property_auction_data['start_date']
                    property_auction.end_date = property_auction_data['end_date'] if "end_date" in property_auction_data else None
                    property_auction.bid_increments = property_auction_data['bid_increments']
                    property_auction.reserve_amount = property_auction_data['reserve_amount'] if "reserve_amount" in property_auction_data else None
                    property_auction.time_zone_id = property_auction_data['time_zone']
                    property_auction.start_price = property_auction_data['start_price']
                    property_auction.insider_decreased_price = property_auction_data['start_price']
                    property_auction.status_id = property_auction_data['auction_status']
                    # property_auction.open_house_start_date = property_auction_data['open_house_start_date']
                    # property_auction.open_house_end_date = property_auction_data['open_house_end_date']
                    property_auction.offer_amount = property_auction_data['offer_amount'] if "offer_amount" in property_auction_data else None
                    property_auction.auction_id = sale_by_type
                    property_auction.domain_id = site_id
                    property_auction.un_priced = un_priced
                    property_auction.required_all = required_all
                    property_auction.insider_price_decrease = property_auction_data['insider_price_decrease'] if "insider_price_decrease" in property_auction_data else None
                    property_auction.dutch_time = int(property_auction_data['dutch_time']) if "dutch_time" in property_auction_data else None
                    property_auction.dutch_end_time = property_auction_data['dutch_end_time'] if "dutch_end_time" in property_auction_data else None
                    property_auction.dutch_pause_time = int(property_auction_data['dutch_pause_time']) if "dutch_pause_time" in property_auction_data else None
                    property_auction.sealed_time = int(property_auction_data['sealed_time']) if "sealed_time" in property_auction_data else None
                    property_auction.sealed_start_time = property_auction_data['sealed_start_time'] if "sealed_start_time" in property_auction_data else None
                    property_auction.sealed_end_time = property_auction_data['sealed_end_time'] if "sealed_end_time" in property_auction_data else None
                    property_auction.sealed_pause_time = int(property_auction_data['sealed_pause_time']) if "sealed_pause_time" in property_auction_data else None
                    property_auction.english_time = int(property_auction_data['english_time']) if "english_time" in property_auction_data else None
                    property_auction.english_start_time = property_auction_data['english_start_time'] if "english_start_time" in property_auction_data else None
                    # property_auction.english_end_time = property_auction_data['english_end_time'] if "english_end_time" in property_auction_data else None


                    property_auction.save()
                # ----------------------Property Subtype---------------------
                if "property_subtype" in data and type(data["property_subtype"]) == list:
                    property_subtype = data["property_subtype"]
                    PropertySubtype.objects.filter(property=property_id).delete()
                    for subtype in property_subtype:
                        property_subtype = PropertySubtype()
                        property_subtype.property_id = property_id
                        property_subtype.subtype_id = subtype
                        property_subtype.save()

                # ----------------------Terms Accepted---------------------
                if "terms_accepted" in data and type(data["terms_accepted"]) == list:
                    terms_accepted = data["terms_accepted"]
                    PropertyTermAccepted.objects.filter(property=property_id).delete()
                    for terms in terms_accepted:
                        property_term_accepted = PropertyTermAccepted()
                        property_term_accepted.property_id = property_id
                        property_term_accepted.term_accepted_id = terms
                        property_term_accepted.save()

                # ----------------------Occupied By---------------------
                if "occupied_by" in data and type(data["occupied_by"]) == list:
                    occupied_by = data["occupied_by"]
                    PropertyOccupiedBy.objects.filter(property=property_id).delete()
                    for occupied in occupied_by:
                        property_occupied_by = PropertyOccupiedBy()
                        property_occupied_by.property_id = property_id
                        property_occupied_by.occupied_by_id = occupied
                        property_occupied_by.save()

                # ----------------------Ownership---------------------
                if "ownership" in data and type(data["ownership"]) == list:
                    ownership = data["ownership"]
                    PropertyOwnership.objects.filter(property=property_id).delete()
                    for owner in ownership:
                        property_ownership = PropertyOwnership()
                        property_ownership.property_id = property_id
                        property_ownership.ownership_id = owner
                        property_ownership.save()

                # ----------------------Possession---------------------
                if "possession" in data and type(data["possession"]) == list:
                    possession = data["possession"]
                    PropertyPossession.objects.filter(property=property_id).delete()
                    for pos in possession:
                        property_possession = PropertyPossession()
                        property_possession.property_id = property_id
                        property_possession.possession_id = pos
                        property_possession.save()

                # ----------------------Style---------------------
                if "style" in data and type(data["style"]) == list:
                    style = data["style"]
                    PropertyStyle.objects.filter(property=property_id).delete()
                    for st in style:
                        property_style = PropertyStyle()
                        property_style.property_id = property_id
                        property_style.style_id = st
                        property_style.save()

                # ----------------------Cooling---------------------
                if "cooling" in data and type(data["cooling"]) == list:
                    cooling = data["cooling"]
                    PropertyCooling.objects.filter(property=property_id).delete()
                    for cool in cooling:
                        property_cooling = PropertyCooling()
                        property_cooling.property_id = property_id
                        property_cooling.cooling_id = cool
                        property_cooling.save()

                # ----------------------Stories---------------------
                if "stories" in data and type(data["stories"]) == list:
                    stories = data["stories"]
                    PropertyStories.objects.filter(property=property_id).delete()
                    for story in stories:
                        property_stories = PropertyStories()
                        property_stories.property_id = property_id
                        property_stories.stories_id = story
                        property_stories.save()

                # ----------------------HeatingStories---------------------
                if "heating" in data and type(data["heating"]) == list:
                    heating = data["heating"]
                    PropertyHeating.objects.filter(property=property_id).delete()
                    for heat in heating:
                        property_heating = PropertyHeating()
                        property_heating.property_id = property_id
                        property_heating.heating_id = heat
                        property_heating.save()

                # ----------------------Electric---------------------
                if "electric" in data and type(data["electric"]) == list:
                    electric = data["electric"]
                    PropertyElectric.objects.filter(property=property_id).delete()
                    for ele in electric:
                        property_electric = PropertyElectric()
                        property_electric.property_id = property_id
                        property_electric.electric_id = ele
                        property_electric.save()

                # ----------------------Gas---------------------
                if "gas" in data and type(data["gas"]) == list:
                    gas = data["gas"]
                    PropertyGas.objects.filter(property=property_id).delete()
                    for g in gas:
                        property_gas = PropertyGas()
                        property_gas.property_id = property_id
                        property_gas.gas_id = g
                        property_gas.save()

                # ----------------------Recent Updates---------------------
                if "recent_updates" in data and type(data["recent_updates"]) == list:
                    recent_updates = data["recent_updates"]
                    PropertyRecentUpdates.objects.filter(property=property_id).delete()
                    for updates in recent_updates:
                        property_recent_updates = PropertyRecentUpdates()
                        property_recent_updates.property_id = property_id
                        property_recent_updates.recent_updates_id = updates
                        property_recent_updates.save()

                # ----------------------Water---------------------
                if "water" in data and type(data["water"]) == list:
                    water = data["water"]
                    PropertyWater.objects.filter(property=property_id).delete()
                    for wa in water:
                        property_water = PropertyWater()
                        property_water.property_id = property_id
                        property_water.water_id = wa
                        property_water.save()

                # ----------------------Security Features---------------------
                if "security_features" in data and type(data["security_features"]) == list:
                    security_features = data["security_features"]
                    PropertySecurityFeatures.objects.filter(property=property_id).delete()
                    for security in security_features:
                        property_security_features = PropertySecurityFeatures()
                        property_security_features.property_id = property_id
                        property_security_features.security_features_id = security
                        property_security_features.save()

                # ----------------------Sewer---------------------
                if "sewer" in data and type(data["sewer"]) == list:
                    sewer = data["sewer"]
                    PropertySewer.objects.filter(property=property_id).delete()
                    for se in sewer:
                        property_sewer = PropertySewer()
                        property_sewer.property_id = property_id
                        property_sewer.sewer_id = se
                        property_sewer.save()

                # ----------------------Tax Exemptions---------------------
                if "tax_exemptions" in data and type(data["tax_exemptions"]) == list:
                    tax_exemptions = data["tax_exemptions"]
                    PropertyTaxExemptions.objects.filter(property=property_id).delete()
                    for tax in tax_exemptions:
                        property_tax_exemptions = PropertyTaxExemptions()
                        property_tax_exemptions.property_id = property_id
                        property_tax_exemptions.tax_exemptions_id = tax
                        property_tax_exemptions.save()

                # ----------------------Zoning---------------------
                if "zoning" in data and type(data["zoning"]) == list:
                    zoning = data["zoning"]
                    PropertyZoning.objects.filter(property=property_id).delete()
                    for zo in zoning:
                        property_zoning = PropertyZoning()
                        property_zoning.property_id = property_id
                        property_zoning.zoning_id = zo
                        property_zoning.save()

                # ----------------------Hoa Amenities---------------------
                if "hoa_amenities" in data and type(data["hoa_amenities"]) == list:
                    hoa_amenities = data["hoa_amenities"]
                    PropertyAmenities.objects.filter(property=property_id).delete()
                    for hoa in hoa_amenities:
                        property_amenities = PropertyAmenities()
                        property_amenities.property_id = property_id
                        property_amenities.amenities_id = hoa
                        property_amenities.save()

                # ----------------------Kitchen Features---------------------
                if "kitchen_features" in data and type(data["kitchen_features"]) == list:
                    kitchen_features = data["kitchen_features"]
                    PropertyKitchenFeatures.objects.filter(property=property_id).delete()
                    for kitchen in kitchen_features:
                        property_kitchen_features = PropertyKitchenFeatures()
                        property_kitchen_features.property_id = property_id
                        property_kitchen_features.kitchen_features_id = kitchen
                        property_kitchen_features.save()

                # ----------------------Appliances---------------------
                if "appliances" in data and type(data["appliances"]) == list:
                    appliances = data["appliances"]
                    PropertyAppliances.objects.filter(property=property_id).delete()
                    for apl in appliances:
                        property_appliances = PropertyAppliances()
                        property_appliances.property_id = property_id
                        property_appliances.appliances_id = apl
                        property_appliances.save()

                # ----------------------Flooring---------------------
                if "flooring" in data and type(data["flooring"]) == list:
                    flooring = data["flooring"]
                    PropertyFlooring.objects.filter(property=property_id).delete()
                    for floor in flooring:
                        property_flooring = PropertyFlooring()
                        property_flooring.property_id = property_id
                        property_flooring.flooring_id = floor
                        property_flooring.save()

                # ----------------------Windows---------------------
                if "windows" in data and type(data["windows"]) == list:
                    windows = data["windows"]
                    PropertyWindows.objects.filter(property=property_id).delete()
                    for window in windows:
                        property_windows = PropertyWindows()
                        property_windows.property_id = property_id
                        property_windows.windows_id = window
                        property_windows.save()

                # ----------------------Bedroom Features---------------------
                if "bedroom_features" in data and type(data["bedroom_features"]) == list:
                    bedroom_features = data["bedroom_features"]
                    PropertyBedroomFeatures.objects.filter(property=property_id).delete()
                    for bedroom in bedroom_features:
                        property_bedroom_features = PropertyBedroomFeatures()
                        property_bedroom_features.property_id = property_id
                        property_bedroom_features.bedroom_features_id = bedroom
                        property_bedroom_features.save()

                # ----------------------Other Rooms---------------------
                if "other_rooms" in data and type(data["other_rooms"]) == list:
                    other_rooms = data["other_rooms"]
                    PropertyOtherRooms.objects.filter(property=property_id).delete()
                    for other in other_rooms:
                        property_other_rooms = PropertyOtherRooms()
                        property_other_rooms.property_id = property_id
                        property_other_rooms.other_rooms_id = other
                        property_other_rooms.save()

                # ----------------------Bathroom Features---------------------
                if "bathroom_features" in data and type(data["bathroom_features"]) == list:
                    bathroom_features = data["bathroom_features"]
                    PropertyBathroomFeatures.objects.filter(property=property_id).delete()
                    for bathroom in bathroom_features:
                        property_bathroom_features = PropertyBathroomFeatures()
                        property_bathroom_features.property_id = property_id
                        property_bathroom_features.bathroom_features_id = bathroom
                        property_bathroom_features.save()
                # ----------------------Other Features---------------------
                if "other_features" in data and type(data["other_features"]) == list:
                    other_features = data["other_features"]
                    PropertyOtherFeatures.objects.filter(property=property_id).delete()
                    for other in other_features:
                        property_other_features = PropertyOtherFeatures()
                        property_other_features.property_id = property_id
                        property_other_features.other_features_id = other
                        property_other_features.save()

                # ----------------------Master Bedroom Features---------------------
                if "master_bedroom_features" in data and type(data["master_bedroom_features"]) == list:
                    master_bedroom_features = data["master_bedroom_features"]
                    PropertyMasterBedroomFeatures.objects.filter(property=property_id).delete()
                    for master_bedroom in master_bedroom_features:
                        property_master_bedroom_features = PropertyMasterBedroomFeatures()
                        property_master_bedroom_features.property_id = property_id
                        property_master_bedroom_features.master_bedroom_features_id = master_bedroom
                        property_master_bedroom_features.save()

                # ----------------------Fireplace Type---------------------
                if "fireplace_type" in data and type(data["fireplace_type"]) == list:
                    fireplace_type = data["fireplace_type"]
                    PropertyFireplaceType.objects.filter(property=property_id).delete()
                    for fireplace in fireplace_type:
                        property_fireplace_type = PropertyFireplaceType()
                        property_fireplace_type.property_id = property_id
                        property_fireplace_type.fireplace_type_id = fireplace
                        property_fireplace_type.save()

                # ----------------------Basement Features---------------------
                if "basement_features" in data and type(data["basement_features"]) == list:
                    basement_features = data["basement_features"]
                    PropertyBasementFeatures.objects.filter(property=property_id).delete()
                    for basement in basement_features:
                        property_basement_features = PropertyBasementFeatures()
                        property_basement_features.property_id = property_id
                        property_basement_features.basement_features_id = basement
                        property_basement_features.save()

                # ----------------------Handicap Amenities---------------------
                if "handicap_amenities" in data and type(data["handicap_amenities"]) == list:
                    handicap_amenities = data["handicap_amenities"]
                    PropertyHandicapAmenities.objects.filter(property=property_id).delete()
                    for amenities in handicap_amenities:
                        property_handicap_amenities = PropertyHandicapAmenities()
                        property_handicap_amenities.property_id = property_id
                        property_handicap_amenities.handicap_amenities_id = amenities
                        property_handicap_amenities.save()

                # ----------------------Construction---------------------
                if "construction" in data and type(data["construction"]) == list:
                    construction = data["construction"]
                    PropertyConstruction.objects.filter(property=property_id).delete()
                    for cons in construction:
                        property_construction = PropertyConstruction()
                        property_construction.property_id = property_id
                        property_construction.construction_id = cons
                        property_construction.save()

                # ----------------------Garage Parking---------------------
                if "garage_parking" in data and type(data["garage_parking"]) == list:
                    garage_parking = data["garage_parking"]
                    PropertyGarageParking.objects.filter(property=property_id).delete()
                    for parking in garage_parking:
                        property_garage_parking = PropertyGarageParking()
                        property_garage_parking.property_id = property_id
                        property_garage_parking.garage_parking_id = parking
                        property_garage_parking.save()

                # ----------------------Exterior Features---------------------
                if "exterior_features" in data and type(data["exterior_features"]) == list:
                    exterior_features = data["exterior_features"]
                    PropertyExteriorFeatures.objects.filter(property=property_id).delete()
                    for exterior in exterior_features:
                        property_exterior_features = PropertyExteriorFeatures()
                        property_exterior_features.property_id = property_id
                        property_exterior_features.exterior_features_id = exterior
                        property_exterior_features.save()

                # ----------------------Garage Features---------------------
                if "garage_features" in data and type(data["garage_features"]) == list:
                    garage_features = data["garage_features"]
                    PropertyGarageFeatures.objects.filter(property=property_id).delete()
                    for garage in garage_features:
                        property_garage_features = PropertyGarageFeatures()
                        property_garage_features.property_id = property_id
                        property_garage_features.garage_features_id = garage
                        property_garage_features.save()

                # ----------------------Roof---------------------
                if "roof" in data and type(data["roof"]) == list:
                    roof = data["roof"]
                    PropertyRoof.objects.filter(property=property_id).delete()
                    for rf in roof:
                        property_roof = PropertyRoof()
                        property_roof.property_id = property_id
                        property_roof.roof_id = rf
                        property_roof.save()

                # ----------------------Outbuildings---------------------
                if "outbuildings" in data and type(data["outbuildings"]) == list:
                    outbuildings = data["outbuildings"]
                    PropertyOutbuildings.objects.filter(property=property_id).delete()
                    for buildings in outbuildings:
                        property_outbuildings = PropertyOutbuildings()
                        property_outbuildings.property_id = property_id
                        property_outbuildings.outbuildings_id = buildings
                        property_outbuildings.save()

                # ----------------------Foundation---------------------
                if "foundation" in data and type(data["foundation"]) == list:
                    foundation = data["foundation"]
                    PropertyFoundation.objects.filter(property=property_id).delete()
                    for fd in foundation:
                        property_foundation = PropertyFoundation()
                        property_foundation.property_id = property_id
                        property_foundation.foundation_id = fd
                        property_foundation.save()

                # ----------------------Location Features---------------------
                if "location_features" in data and type(data["location_features"]) == list:
                    location_features = data["location_features"]
                    PropertyLocationFeatures.objects.filter(property=property_id).delete()
                    for location in location_features:
                        property_location_features = PropertyLocationFeatures()
                        property_location_features.property_id = property_id
                        property_location_features.location_features_id = location
                        property_location_features.save()

                # ----------------------Fence---------------------
                if "fence" in data and type(data["fence"]) == list:
                    fence = data["fence"]
                    PropertyFence.objects.filter(property=property_id).delete()
                    for fnc in fence:
                        property_fence = PropertyFence()
                        property_fence.property_id = property_id
                        property_fence.fence_id = fnc
                        property_fence.save()

                # ----------------------Road Frontage---------------------
                if "road_frontage" in data and type(data["road_frontage"]) == list:
                    road_frontage = data["road_frontage"]
                    PropertyRoadFrontage.objects.filter(property=property_id).delete()
                    for frontage in road_frontage:
                        property_road_frontage = PropertyRoadFrontage()
                        property_road_frontage.property_id = property_id
                        property_road_frontage.road_frontage_id = frontage
                        property_road_frontage.save()

                # ----------------------Pool---------------------
                if "pool" in data and type(data["pool"]) == list:
                    pool = data["pool"]
                    PropertyPool.objects.filter(property=property_id).delete()
                    for pl in pool:
                        property_pool = PropertyPool()
                        property_pool.property_id = property_id
                        property_pool.pool_id = pl
                        property_pool.save()

                # ----------------------Property Faces---------------------
                if "property_faces" in data and type(data["property_faces"]) == list:
                    property_faces = data["property_faces"]
                    PropertyPropertyFaces.objects.filter(property=property_id).delete()
                    for faces in property_faces:
                        property_property_faces = PropertyPropertyFaces()
                        property_property_faces.property_id = property_id
                        property_property_faces.property_faces_id = faces
                        property_property_faces.save()

                # ----------------Commercial------------------

                # ----------------------Property Faces---------------------
                if "lease_type" in data and type(data["lease_type"]) == list:
                    lease_type = data["lease_type"]
                    PropertyLeaseType.objects.filter(property=property_id).delete()
                    for lease in lease_type:
                        property_lease_type = PropertyLeaseType()
                        property_lease_type.property_id = property_id
                        property_lease_type.lease_type_id = lease
                        property_lease_type.save()

                # ----------------------Tenant Pays---------------------
                if "tenant_pays" in data and type(data["tenant_pays"]) == list:
                    tenant_pays = data["tenant_pays"]
                    PropertyTenantPays.objects.filter(property=property_id).delete()
                    for tenant in tenant_pays:
                        property_tenant_pays = PropertyTenantPays()
                        property_tenant_pays.property_id = property_id
                        property_tenant_pays.tenant_pays_id = tenant
                        property_tenant_pays.save()

                # ----------------------Tenant Pays---------------------
                if "tenant_pays" in data and type(data["tenant_pays"]) == list:
                    tenant_pays = data["tenant_pays"]
                    PropertyTenantPays.objects.filter(property=property_id).delete()
                    for tenant in tenant_pays:
                        property_tenant_pays = PropertyTenantPays()
                        property_tenant_pays.property_id = property_id
                        property_tenant_pays.tenant_pays_id = tenant
                        property_tenant_pays.save()

                # ----------------------Inclusions---------------------
                if "inclusions" in data and type(data["inclusions"]) == list:
                    inclusions = data["inclusions"]
                    PropertyInclusions.objects.filter(property=property_id).delete()
                    for incl in inclusions:
                        property_inclusions = PropertyInclusions()
                        property_inclusions.property_id = property_id
                        property_inclusions.inclusions_id = incl
                        property_inclusions.save()

                # ----------------------Building Class---------------------
                if "building_class" in data and type(data["building_class"]) == list:
                    building_class = data["building_class"]
                    PropertyBuildingClass.objects.filter(property=property_id).delete()
                    for building in building_class:
                        property_building_class = PropertyBuildingClass()
                        property_building_class.property_id = property_id
                        property_building_class.building_class_id = building
                        property_building_class.save()

                # ----------------------Interior Features---------------------
                if "interior_features" in data and type(data["interior_features"]) == list:
                    interior_features = data["interior_features"]
                    PropertyInteriorFeatures.objects.filter(property=property_id).delete()
                    for interior in interior_features:
                        property_interior_features = PropertyInteriorFeatures()
                        property_interior_features.property_id = property_id
                        property_interior_features.interior_features_id = interior
                        property_interior_features.save()

                # ------------------Land-----------------
                # ----------------------Mineral Rights---------------------
                if "mineral_rights" in data and type(data["mineral_rights"]) == list:
                    mineral_rights = data["mineral_rights"]
                    PropertyMineralRights.objects.filter(property=property_id).delete()
                    for mineral in mineral_rights:
                        property_mineral_rights = PropertyMineralRights()
                        property_mineral_rights.property_id = property_id
                        property_mineral_rights.mineral_rights_id = mineral
                        property_mineral_rights.save()

                # ----------------------Easements---------------------
                if "easements" in data and type(data["easements"]) == list:
                    easements = data["easements"]
                    PropertyEasements.objects.filter(property=property_id).delete()
                    for eas in easements:
                        property_easements = PropertyEasements()
                        property_easements.property_id = property_id
                        property_easements.easements_id = eas
                        property_easements.save()

                # ----------------------Survey---------------------
                if "survey" in data and type(data["survey"]) == list:
                    survey = data["survey"]
                    PropertySurvey.objects.filter(property=property_id).delete()
                    for sur in survey:
                        property_survey = PropertySurvey()
                        property_survey.property_id = property_id
                        property_survey.survey_id = sur
                        property_survey.save()

                # ----------------------Utilities---------------------
                if "utilities" in data and type(data["utilities"]) == list:
                    utilities = data["utilities"]
                    PropertyUtilities.objects.filter(property=property_id).delete()
                    for uti in utilities:
                        property_utilities = PropertyUtilities()
                        property_utilities.property_id = property_id
                        property_utilities.utilities_id = uti
                        property_utilities.save()

                # ----------------------Improvements---------------------
                if "improvements" in data and type(data["improvements"]) == list:
                    improvements = data["improvements"]
                    PropertyImprovements.objects.filter(property=property_id).delete()
                    for imp in improvements:
                        property_improvements = PropertyImprovements()
                        property_improvements.property_id = property_id
                        property_improvements.improvements_id = imp
                        property_improvements.save()

                # ----------------------Topography---------------------
                if "topography" in data and type(data["topography"]) == list:
                    topography = data["topography"]
                    PropertyTopography.objects.filter(property=property_id).delete()
                    for top in topography:
                        property_topography = PropertyTopography()
                        property_topography.property_id = property_id
                        property_topography.topography_id = top
                        property_topography.save()

                # ----------------------Wildlife---------------------
                if "wildlife" in data and type(data["wildlife"]) == list:
                    wildlife = data["wildlife"]
                    PropertyWildlife.objects.filter(property=property_id).delete()
                    for wild in wildlife:
                        property_wildlife = PropertyWildlife()
                        property_wildlife.property_id = property_id
                        property_wildlife.wildlife_id = wild
                        property_wildlife.save()

                # ----------------------Fish---------------------
                if "fish" in data and type(data["fish"]) == list:
                    fish = data["fish"]
                    PropertyFish.objects.filter(property=property_id).delete()
                    for fi in fish:
                        property_fish = PropertyFish()
                        property_fish.property_id = property_id
                        property_fish.fish_id = fi
                        property_fish.save()

                # ----------------------Irrigation System---------------------
                if "irrigation_system" in data and type(data["irrigation_system"]) == list:
                    irrigation_system = data["irrigation_system"]
                    PropertyIrrigationSystem.objects.filter(property=property_id).delete()
                    for irrigation in irrigation_system:
                        property_irrigation_system = PropertyIrrigationSystem()
                        property_irrigation_system.property_id = property_id
                        property_irrigation_system.irrigation_system_id = irrigation
                        property_irrigation_system.save()

                # ----------------------Recreation---------------------
                if "recreation" in data and type(data["recreation"]) == list:
                    recreation = data["recreation"]
                    PropertyRecreation.objects.filter(property=property_id).delete()
                    for rec in recreation:
                        property_recreation = PropertyRecreation()
                        property_recreation.property_id = property_id
                        property_recreation.recreation_id = rec
                        property_recreation.save()

                # ----------------------Property opening date---------------------
                if property_asset != 1:
                    if "property_opening_dates" in data and type(data["property_opening_dates"]) == list:
                        property_opening_dates = data["property_opening_dates"]
                        PropertyOpening.objects.filter(property=property_id).delete()
                        for dates in property_opening_dates:
                            property_opening = PropertyOpening()
                            property_opening.domain_id = site_id
                            property_opening.property_id = property_id
                            property_opening.opening_start_date = dates['start_date'] if dates['start_date'] != "" else None
                            property_opening.opening_end_date = dates['end_date'] if dates['end_date'] != "" else None
                            property_opening.status_id = 1
                            property_opening.save()

                try:
                    property_listing = PropertyListing.objects.get(id=property_id)
                except:
                    pass

            elif step == 2:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "is_map_view" in data and data["is_map_view"] != "":
                    is_map_view = data["is_map_view"]
                else:
                    return Response(response.parsejson("is_map_view is required.", "", status=403))

                if "is_street_view" in data and data["is_street_view"] != "":
                    is_street_view = data["is_street_view"]
                else:
                    return Response(response.parsejson("is_street_view is required.", "", status=403))

                if "is_arial_view" in data and data["is_arial_view"] != "":
                    is_arial_view = data["is_arial_view"]
                else:
                    return Response(response.parsejson("is_arial_view is required.", "", status=403))

                map_url = None
                if "map_url" in data and data['map_url'] != "":
                    map_url = data['map_url']
                # else:
                #     return Response(response.parsejson("map_url is required.", "", status=403))

                latitude = None
                if "latitude" in data and data['latitude'] != "":
                    latitude = data['latitude']

                longitude = None
                if "longitude" in data and data['longitude'] != "":
                    longitude = data['longitude']

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.is_map_view = is_map_view
                property_listing.is_street_view = is_street_view
                property_listing.is_arial_view = is_arial_view
                property_listing.create_step = 2
                property_listing.map_url = map_url
                property_listing.latitude = latitude
                property_listing.longitude = longitude
                property_listing.save()
            elif step == 3:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "property_pic" in data and type(data["property_pic"]) == list and len(data["property_pic"]) > 0:
                    property_pic = data["property_pic"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=1).delete()
                    for pic in property_pic:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = pic
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 1
                        property_uploads.status_id = 1
                        property_uploads.save()

                if "property_video" in data and type(data["property_video"]) == list and len(data["property_video"]) > 0:
                    property_video = data["property_video"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=2).delete()
                    for video in property_video:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = video
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 2
                        property_uploads.status_id = 1
                        property_uploads.save()

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.create_step = 3
                property_listing.save()
            elif step == 4:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "property_documents" in data and type(data["property_documents"]) == list and len(data["property_documents"]) > 0:
                    property_documents = data["property_documents"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=3).delete()
                    for documents in property_documents:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = documents
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 3
                        property_uploads.status_id = 1
                        property_uploads.save()

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.create_step = 4
                property_listing.save()
            property_auction_data = PropertyAuction.objects.filter(property=property_id).last()
            all_data = {"property_id": property_id, "auction_id": property_auction_data.id, "auction_type": property_auction_data.auction_id}
            # ----------------------------Email----------------------------------------
            if check_update is None:
                property_detail = property_listing
                user_detail = property_listing.agent
                property_user_name = user_detail.first_name
                agent_email = user_detail.email
                agent_phone = user_detail.phone_no if user_detail.phone_no is not None else ""
                auction_type = property_detail.sale_by_type.auction_type
                auction_data = PropertyAuction.objects.get(property=property_id)
                start_price = auction_data.start_price
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+str(bucket_name)+'/'+str(image)
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/"
                notif_type = 2
                if property_detail.sale_by_type_id == 7:
                    domain_url = domain_url + "?auction_type=highest%20offer"
                    notif_type =  6
                elif property_detail.sale_by_type_id == 4:
                    domain_url = domain_url + "?auction_type=traditional%20offer"
                    notif_type =  4
                elif property_detail.sale_by_type_id == 6:
                    domain_url = domain_url + "?auction_type=live%20offer"
                    notif_type =  7
                elif property_detail.sale_by_type_id == 2:
                    domain_url = domain_url + "?auction_type=insider%20auction"
                    notif_type =  8
                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                asset_type = property_detail.property_asset.name
                template_data = {"domain_id": site_id, "slug": "add_listing"}
                extra_data = {
                    'property_user_name': property_user_name,
                    'web_url': web_url,
                    'property_image': image_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'auction_type': auction_type,
                    'asset_type': asset_type,
                    'starting_price': "$" + str(number_format(start_price)) if not auction_data.un_priced else 'Unpriced',
                    'starting_bid_offer': 'Starting Bid' if property_detail.sale_by_type_id in [1, 6] else "Asking Price",
                    'dashboard_link': domain_url,
                    "domain_id": site_id
                }
                compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                #=============send email to broker==============
                broker_detail = Users.objects.get(site_id=site_id)
                broker_name = broker_detail.first_name if broker_detail.first_name is not None else ""
                broker_email = broker_detail.email if broker_detail.email is not None else ""
                if broker_email.lower() != agent_email.lower():
                    try:
                        #send email to broker
                        template_data = {"domain_id": site_id, "slug": "add_listing_broker"}
                        extra_data = {
                            'property_user_name': broker_name,
                            'web_url': web_url,
                            'property_image': image_url,
                            'property_address': property_address,
                            'property_city': property_city,
                            'property_state': property_state,
                            'auction_type': auction_type,
                            'asset_type': asset_type,
                            'starting_price': "$" + str(number_format(start_price)) if not auction_data.un_priced else 'Unpriced',
                            'starting_bid_offer': 'Starting Bid' if property_detail.sale_by_type_id in [1, 6] else "Asking Price",
                            'dashboard_link': domain_url,
                            "domain_id": site_id,
                            'domain_name': domain_name,
                            'agent_name': property_user_name,
                            'agent_email': agent_email,
                            'agent_phone': phone_format(agent_phone)
                        }
                        compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                    except Exception as e:
                        pass
                    
                try:
                    prop_name = property_detail.address_one if property_detail.address_one else str(property_detail.id)
                    # check if domain owner/broker is adding
                    if broker_detail.id != user_id:
                        # send notif to broker person to review
                        content = "A new listing is created for review! <span>[" + prop_name + "]</span>"
                        add_notification(
                            site_id,
                            "Create Listing",
                            content,
                            user_id=broker_detail.id,
                            added_by=broker_detail.id,
                            notification_for=2,
                            property_id=property_id,
                            notification_type=notif_type
                        )
                        #  add notif to agent
                        content = "Your listing is submitted for review! <span>[" + prop_name + "]</span>"
                        add_notification(
                            site_id,
                            "Create Listing",
                            content,
                            user_id=user_id,
                            added_by=user_id,
                            notification_for=2,
                            property_id=property_id,
                            notification_type=notif_type
                        )
                    else:
                        # send notif to broker person to review
                        content = "You have created a new listing! <span>[" + prop_name + "]</span>"
                        add_notification(
                            site_id,
                            "Create Listing",
                            content,
                            user_id=broker_detail.id,
                            added_by=broker_detail.id,
                            notification_for=2,
                            property_id=property_id,
                            notification_type=notif_type
                        )
                except Exception as e:
                    pass

            return Response(response.parsejson("Property added/updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AssetListingApiView(APIView):
    """
    Asset Listing
    """
    authentication_classes = [TokenAuthentication, OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            all_data = get_cache("property_asset")
            if all_data is None:
                data = request.data
                all_data = LookupPropertyAsset.objects.filter(is_active=1).order_by("-id").values("id", "name")
                set_cache("property_asset", all_data)

            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTypeListingApiView(APIView):
    """
    Property type Listing
    """
    authentication_classes = [TokenAuthentication,OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_type"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupPropertyType.objects.filter(is_active=1)
                if asset_id is not None:
                    all_data = all_data.filter(asset=asset_id)
                all_data = all_data.order_by("-id").values("id", name=F("property_type"))
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertySubTypeListingApiView(APIView):
    """
    Property subtype Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_subtype"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupPropertySubType.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTermsAcceptedListingApiView(APIView):
    """
    Property terms accepted Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_terms_accepted"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupTermsAccepted.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyOccupiedByListingApiView(APIView):
    """
    Property occupied by Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_occupied_by"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupOccupiedBy.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyOwnershipListingApiView(APIView):
    """
    Property ownership Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_ownership"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupOwnership.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyPossessionListingApiView(APIView):
    """
    Property possession Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_possession"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupPossession.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)

            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyLotSizeListingApiView(APIView):
    """
    Property lot size Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_lot_size"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupLotSize.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyStyleListingApiView(APIView):
    """
    Property style Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_style"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupStyle.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyCoolingListingApiView(APIView):
    """
    Property cooling Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_cooling"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupCooling.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyStoriesListingApiView(APIView):
    """
    Property stories Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_stories"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupStories.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyHeatingListingApiView(APIView):
    """
    Property heating Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_heating"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupHeating.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyElectricListingApiView(APIView):
    """
    Property electric Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_electric"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupElectric.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyGasListingApiView(APIView):
    """
    Property gas Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_gas"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupGas.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyRecentUpdateListingApiView(APIView):
    """
    Property recent update Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_recent_update"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupRecentUpdates.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyWaterListingApiView(APIView):
    """
    Property recent update Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_water"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupWater.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertySecurityFeaturesListingApiView(APIView):
    """
    Property security features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_security_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupSecurityFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)

            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertySewerListingApiView(APIView):
    """
    Property sewer Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_sewer"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupSewer.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTaxExemptionsListingApiView(APIView):
    """
    Property tax exemptions Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_tax_exemptions"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupTaxExemptions.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyZoningListingApiView(APIView):
    """
    Property zoning Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_zoning"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupZoning.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyAmenitiesListingApiView(APIView):
    """
    Property amenities Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_amenities"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupAmenities.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyKitchenFeaturesListingApiView(APIView):
    """
    Property kitchen features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_kitchen_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupKitchenFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyAppliancesListingApiView(APIView):
    """
    Property appliances Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_appliances"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupAppliances.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFlooringListingApiView(APIView):
    """
    Property flooring Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_flooring"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupFlooring.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyWindowsListingApiView(APIView):
    """
    Property windows Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_windows"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupWindows.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyBedroomFeaturesListingApiViews(APIView):
    """
    Property Bedroom Features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_bedroom_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupBedroomFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyOtherRoomsListingApiView(APIView):
    """
    Property other rooms Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_other_rooms"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupOtherRooms.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyBathroomFeaturesListingApiView(APIView):
    """
    Property bathroom features rooms Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_bathroom_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupBathroomFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyOtherFeaturesListingApiView(APIView):
    """
    Property other features rooms Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_other_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupOtherFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyMasterBedroomListingApiView(APIView):
    """
    Property master bedroom features rooms Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_master_bedroom_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupMasterBedroomFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFireplaceTypeListingApiView(APIView):
    """
    Property fireplace type Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_fireplace_type"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupFireplaceType.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyBasementFeaturesListingApiView(APIView):
    """
    Property basement features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_basement_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupBasementFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyHandicapAmenitiesListingApiView(APIView):
    """
    Property handicap amenities Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_handicap_amenities"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupHandicapAmenities.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyConstructionListingApiView(APIView):
    """
    Property construction Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_construction"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupConstruction.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyGarageParkingListingApiView(APIView):
    """
    Property garage parking Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_garage_parking"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupGarageParking.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyExteriorFeaturesListingApiView(APIView):
    """
    Property exterior features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_exterior_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupExteriorFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyGarageFeaturesListingApiView(APIView):
    """
    Property garage features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_garage_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupGarageFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyRoofListingApiView(APIView):
    """
    Property roof Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_roof"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupRoof.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyOutbuildingsListingApiView(APIView):
    """
    Property outbuildings Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_outbuildings"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupOutbuildings.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFoundationListingApiView(APIView):
    """
    Property foundation Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_foundation"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupFoundation.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyLocationFeaturesListingApiView(APIView):
    """
    Property location features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_location_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupLocationFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFencesListingApiView(APIView):
    """
    Property fences Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_fences"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupFence.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyRoadFrontageListingApiView(APIView):
    """
    Property road frontage Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_road_frontage"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupRoadFrontage.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyPoolListingApiView(APIView):
    """
    Property pool Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_pool"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupPool.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyPropertyFacesListingApiView(APIView):
    """
    Property property faces Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_property_faces"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupPropertyFaces.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyLeaseTypeListingApiView(APIView):
    """
    Property lease type Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_lease_type"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupLeaseType.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTenantPaysListingApiView(APIView):
    """
    Property tenant pays Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_tenant_pays"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupTenantPays.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyInclusionsListingApiView(APIView):
    """
    Property inclusions Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_inclusions"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupInclusions.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyBuildingClassListingApiView(APIView):
    """
    Property building class Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_building_class"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupBuildingClass.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyInteriorFeaturesListingApiView(APIView):
    """
    Property interior features Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_interior_features"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupInteriorFeatures.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyMineralRightsListingApiView(APIView):
    """
    Property mineral rights Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_mineral_rights"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupMineralRights.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEasementsListingApiView(APIView):
    """
    Property easements Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_easements"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupEasements.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertySurveyListingApiView(APIView):
    """
    Property survey Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_survey"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupSurvey.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyUtilitiesListingApiView(APIView):
    """
    Property utilities Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_utilities"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupUtilities.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyImprovementsListingApiView(APIView):
    """
    Property improvements Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_improvements"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupImprovements.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTopographyListingApiView(APIView):
    """
    Property topography Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_topography"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupTopography.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyWildlifeListingApiView(APIView):
    """
    Property wildlife Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_wildlife"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupWildlife.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFishListingApiView(APIView):
    """
    Property fish Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_fish"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupFish.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyIrrigationSystemListingApiView(APIView):
    """
    Property irrigation system Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_irrigation_system"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupIrrigationSystem.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyRecreationListingApiView(APIView):
    """
    Property recreation Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            asset_id = None
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            cache_name = "property_recreation"
            if asset_id is not None:
                cache_name = cache_name + "_" + str(asset_id)
            all_data = get_cache(cache_name)
            if all_data is None:
                all_data = LookupRecreation.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                set_cache(cache_name, all_data)
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyListingApiView(APIView):
    """
    Property listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))
            user_domain = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                is_agent = None
                if users is None:
                    is_agent = True
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                data["agent"] = user_id
                user_domain = users.site_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            property_listing = PropertyListing.objects.filter(domain=site_id).exclude(status=5)
            if is_agent is not None:
                property_listing = property_listing.filter(agent=user_id)

            # -----------------Filter-------------------
            
            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_listing = property_listing.filter(Q(agent=agent_id))
            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_listing = property_listing.filter(Q(sale_by_type=auction_id))

            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                property_listing = property_listing.filter(Q(property_asset=asset_id))

            if "status" in data and data["status"] != "":
                status = int(data["status"])
                property_listing = property_listing.filter(Q(status=status))

            if "property_type" in data and data["property_type"] != "":
                property_type = int(data["property_type"])
                property_listing = property_listing.filter(Q(property_type=property_type))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_listing = property_listing.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_listing = property_listing.annotate(property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '), 'postal_code', output_field=CharField())).annotate(full_name=Concat('agent__user_business_profile__first_name', V(' '), 'agent__user_business_profile__last_name')).filter(Q(property_asset__name__icontains=search) | Q(sale_by_type__auction_type__icontains=search) | Q(agent__user_business_profile__company_name__icontains=search) | Q(full_name__icontains=search) | Q(city__icontains=search) | Q(address_one__icontains=search) | Q(state__state_name__icontains=search) | Q(property_type__property_type__icontains=search) | Q(property_name__icontains=search) | Q(postal_code__icontains=search))

            total = property_listing.count()
            property_listing = property_listing.order_by(F("ordering").asc(nulls_last=True)).only("id")[offset:limit]
            serializer = PropertyListingSerializer(property_listing, many=True)
            all_data = {"data": serializer.data, "total": total, "user_domain": user_domain}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPropertyListingApiView(APIView):
    """
    Admin property listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            property_listing = PropertyListing.objects.exclude(status=5)
            # -----------------Filter-------------------
            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_listing = property_listing.filter(agent=agent_id)
            if "user_id" in data and type(data['user_id']) == list and len(data['user_id']) > 0:
                user_id = data["user_id"]
                property_listing = property_listing.filter(agent__in=user_id)

            if "site_id" in data and type(data['site_id']) == list and len(data['site_id']) > 0:
                site_id = data["site_id"]
                property_listing = property_listing.filter(domain__in=site_id)

            if "auction_id" in data and type(data['auction_id']) == list and len(data['auction_id']) > 0:
                auction_id = data["auction_id"]
                property_listing = property_listing.filter(Q(sale_by_type__in=auction_id))

            if "asset_id" in data and type(data['asset_id']) == list and len(data['asset_id']) > 0:
                asset_id = data["asset_id"]
                property_listing = property_listing.filter(Q(property_asset__in=asset_id))

            if "asset_sub_type" in data and type(data['asset_sub_type']) == list and len(data['asset_sub_type']) > 0:
                asset_sub_type = data["asset_sub_type"]
                property_listing = property_listing.filter(Q(property_type__in=asset_sub_type))

            if "status" in data and type(data['status']) == list and len(data['status']) > 0:
                status = data["status"]
                property_listing = property_listing.filter(Q(status__in=status))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    property_listing = property_listing\
                        .annotate(property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '), 'postal_code', output_field=CharField()))\
                        .filter(
                            Q(id=search) |
                            Q(agent__user_business_profile__company_name__icontains=search) | 
                            Q(property_name__icontains=search)
                        )
                else:
                    property_listing = property_listing\
                        .annotate(property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '), 'postal_code', output_field=CharField()))\
                        .annotate(full_name=Concat('agent__user_business_profile__first_name', V(' '), 'agent__user_business_profile__last_name'))\
                        .filter(
                                Q(sale_by_type__auction_type__icontains=search) |
                                Q(agent__user_business_profile__company_name__icontains=search) |
                                Q(agent__user_business_profile__first_name__icontains=search) |
                                Q(agent__user_business_profile__last_name__icontains=search) |
                                Q(full_name__icontains=search) |
                                Q(property_name__icontains=search)
                        )

            total = property_listing.count()
            property_listing = property_listing.order_by("-id").only("id")[offset:limit]
            serializer = AdminPropertyListingSerializer(property_listing, many=True)
            all_data = {"data": serializer.data, "total": total}

            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainPropertyDetailApiView(APIView):
    """
    Subdomain property detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "step_id" in data and data['step_id'] != "":
                step_id = int(data['step_id'])
            else:
                return Response(response.parsejson("step_id is required", "", status=403))
            property_listing = PropertyListing.objects.get(id=property_id, domain=site_id)
            if step_id == 1:
                serializer = PropertyDetailStepOneSerializer(property_listing)
            elif step_id == 2:
                serializer = PropertyDetailStepTwoSerializer(property_listing)
            elif step_id == 3:
                serializer = PropertyDetailStepThreeSerializer(property_listing)
            elif step_id == 4:
                serializer = PropertyDetailStepFourSerializer(property_listing)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainAddPropertyVideoApiView(APIView):
    """
    Subdomain add property video
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1,
                                                 network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "video_url" in data and data['video_url'] != "":
                video_url = data['video_url']
            else:
                return Response(response.parsejson("video_url is required.", "", status=403))

            user_uploads = UserUploads()
            user_uploads.user_id = user_id
            user_uploads.site_id = site_id
            user_uploads.doc_file_name = video_url
            user_uploads.added_by_id = user_id
            user_uploads.updated_by_id = user_id
            user_uploads.save()
            upload_id = user_uploads.id
            all_data = {"upload_id": upload_id, "video_url": video_url}
            return Response(response.parsejson("Video added successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminAddPropertyVideoApiView(APIView):
    """
    Admin add property video
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "video_url" in data and data['video_url'] != "":
                video_url = data['video_url']
            else:
                return Response(response.parsejson("video_url is required.", "", status=403))

            user_uploads = UserUploads()
            user_uploads.user_id = admin_id
            user_uploads.site_id = site_id
            user_uploads.doc_file_name = video_url
            user_uploads.added_by_id = admin_id
            user_uploads.updated_by_id = admin_id
            user_uploads.save()
            upload_id = user_uploads.id
            all_data = {"upload_id": upload_id, "video_url": video_url}
            return Response(response.parsejson("Video added successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainPropertyDocumentDeleteApiView(APIView):
    """
    Subdomain property document delete
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1,
                                                 network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_id = PropertyListing.objects.filter(id=property_id, domain=site_id).first()
                if property_id is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required.", "", status=403))

            PropertyUploads.objects.filter(upload=upload_id, property=property_id, property__domain=site_id).delete()
            UserUploads.objects.filter(id=upload_id, site=site_id).delete()
            return Response(response.parsejson("Delete successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPropertyDocumentDeleteApiView(APIView):
    """
    Admin property document delete
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                property_id = PropertyListing.objects.filter(id=property_id).first()
                if property_id is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required.", "", status=403))

            PropertyUploads.objects.filter(upload=upload_id, property=property_id).delete()
            UserUploads.objects.filter(id=upload_id).delete()
            return Response(response.parsejson("Delete successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyFeaturesApiView(APIView):
    """
    Add property features
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
            data = request.data
            if "feature_type" in data and data['feature_type'] != "":
                feature_type = data['feature_type'].strip()
                feature_table = features_table[feature_type]
            else:
                return Response(response.parsejson("feature_type is required.", "", status=403))

            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            else:
                return Response(response.parsejson("asset_id is required.", "", status=403))

            if "name" in data and data['name'] != "":
                name = data['name'].strip()
                if feature_type == "property_type":
                    check_name = feature_table.objects.filter(property_type=name, asset=asset_id).first()
                else:
                    check_name = feature_table.objects.filter(name=name, asset=asset_id).first()
                if check_name is not None:
                    all_data = {"feature_id": check_name.id}
                    return Response(response.parsejson("Feature added successfully.", all_data, status=201))
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            feature = feature_table()
            if feature_type == "property_type":
                feature.property_type = name
            else:
                feature.name = name
            feature.asset_id = asset_id
            feature.is_active = 1
            feature.save()
            feature_id = feature.id
            all_data = {"feature_id": feature_id}
            return Response(response.parsejson("Feature added successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyFeaturesListingsApiView(APIView):
    """
    Add property features
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            features_table = {
                "property_type": LookupPropertyType,
                "property_subtype": LookupPropertySubType,
                "terms_accepted": LookupTermsAccepted,
                "occupied_by": LookupOccupiedBy,
                "ownership": LookupOwnership,
                "possession": LookupPossession,
                "lot_size": LookupLotSize,
                "style": LookupStyle,
                "cooling": LookupCooling,
                "stories": LookupStories,
                "heating": LookupHeating,
                "electric": LookupElectric,
                "gas": LookupGas,
                "recent_updates": LookupRecentUpdates,
                "water": LookupWater,
                "security_features": LookupSecurityFeatures,
                "sewer": LookupSewer,
                "tax_exemptions": LookupTaxExemptions,
                "zoning": LookupZoning,
                "amenities": LookupAmenities,
                "kitchen_features": LookupKitchenFeatures,
                "appliances": LookupAppliances,
                "flooring": LookupFlooring,
                "windows": LookupWindows,
                "bedroom_features": LookupBedroomFeatures,
                "bathroom_features": LookupBathroomFeatures,
                "other_rooms": LookupOtherRooms,
                "other_features": LookupOtherFeatures,
                "master_bedroom_features": LookupMasterBedroomFeatures,
                "fireplace_type": LookupFireplaceType,
                "basement_features": LookupBasementFeatures,
                "handicap_amenities": LookupHandicapAmenities,
                "construction": LookupConstruction,
                "exterior_features": LookupExteriorFeatures,
                "garage_parking": LookupGarageParking,
                "garage_features": LookupGarageFeatures,
                "roof": LookupRoof,
                "outbuildings": LookupOutbuildings,
                "foundation": LookupFoundation,
                "location_features": LookupLocationFeatures,
                "fence": LookupFence,
                "road_frontage": LookupRoadFrontage,
                "pool": LookupPool,
                "property_faces": LookupPropertyFaces,
                "lease_type": LookupLeaseType,
                "tenant_pays": LookupTenantPays,
                "inclusions": LookupInclusions,
                "building_class": LookupBuildingClass,
                "interior_features": LookupInteriorFeatures,
                "mineral_rights": LookupMineralRights,
                "easements": LookupEasements,
                "survey": LookupSurvey,
                "utilities": LookupUtilities,
                "improvements": LookupImprovements,
                "topography": LookupTopography,
                "wildlife": LookupWildlife,
                "fish": LookupFish,
                "irrigation_system": LookupIrrigationSystem,
                "recreation": LookupRecreation,
            }
            data = request.data
            if "asset_id" in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            else:
                return Response(response.parsejson("asset_id is required.", "", status=403))

            all_data = {}
            for key, values in features_table.items():
                if key == "property_type":
                    features = values.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", name=F("property_type"))
                else:
                    features = values.objects.filter(asset=asset_id, is_active=1).order_by("-id").values("id", "name")
                all_data[key] = features

            auction_type = LookupAuctionType.objects.filter(is_active=1).order_by("id").values("id", "auction_type")
            all_data["auction_type"] = auction_type
            
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminAddPropertyApiView(APIView):
    """
    Admin add/update Property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            property_id = None
            check_update = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
                check_update = True
                property_id = PropertyListing.objects.filter(id=property_id).first()
                if property_id is None:
                    return Response(response.parsejson("Property not exist.", "", status=403))

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                if property_id is None:
                    return Response(response.parsejson("site_id is required", "", status=403))

            if "step" in data and data['step'] != "":
                step = int(data['step'])
            else:
                return Response(response.parsejson("step is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                data["agent"] = user_id
            else:
                if step == 1:
                    return Response(response.parsejson("user_id is required.", "", status=403))

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                admin_users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if admin_users is None:
                    return Response(response.parsejson("Super admin not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if step == 1:
                un_priced = 0
                if "un_priced" in data and data['un_priced'] != "":
                    un_priced = int(data['un_priced'])

                required_all = 0
                if "required_all" in data and data['required_all'] != "":
                    required_all = int(data['required_all'])

                if "property_asset" in data and data['property_asset'] != "":
                    property_asset = int(data['property_asset'])
                    asset = LookupPropertyAsset.objects.filter(id=property_asset, is_active=1).first()
                    if asset is None:
                        return Response(response.parsejson("Property asset not available.", "", status=403))
                else:
                    return Response(response.parsejson("property_asset is required.", "", status=403))

                if "address_one" in data and data['address_one'] != "":
                    address_one = data['address_one']
                else:
                    return Response(response.parsejson("address_one is required.", "", status=403))

                if "city" in data and data['city'] != "":
                    city = data['city']
                else:
                    return Response(response.parsejson("city is required.", "", status=403))

                if "state" in data and data['state'] != "":
                    state = int(data['state'])
                else:
                    return Response(response.parsejson("state is required.", "", status=403))

                if "postal_code" in data and data['postal_code'] != "":
                    postal_code = int(data['postal_code'])
                else:
                    return Response(response.parsejson("postal_code is required.", "", status=403))

                if "property_type" in data and data['property_type'] != "":
                    property_type = int(data['property_type'])
                else:
                    return Response(response.parsejson("property_type is required.", "", status=403))

                if "sale_by_type" in data and data['sale_by_type'] != "":
                    sale_by_type = int(data['sale_by_type'])
                else:
                    return Response(response.parsejson("sale_by_type is required.", "", status=403))

                if sale_by_type == 6:
                    if "auction_location" in data and data['auction_location'] != "":
                        auction_location = data['auction_location']
                    else:
                        return Response(response.parsejson("auction_location is required.", "", status=403))

                if sale_by_type == 7 and required_all == 1:
                    if "due_diligence_period" in data and data['due_diligence_period'] != "":
                        due_diligence_period = int(data['due_diligence_period'])
                    else:
                        return Response(response.parsejson("due_diligence_period is required.", "", status=403))

                    if "escrow_period" in data and data['escrow_period'] != "":
                        escrow_period = int(data['escrow_period'])
                    else:
                        return Response(response.parsejson("escrow_period is required.", "", status=403))

                    if "earnest_deposit" in data and data['earnest_deposit'] != "":
                        earnest_deposit = data['earnest_deposit']
                    else:
                        return Response(response.parsejson("earnest_deposit is required.", "", status=403))

                    if "earnest_deposit_type" in data and data['earnest_deposit_type'] != "":
                        earnest_deposit_type = int(data['earnest_deposit_type'])
                    else:
                        return Response(response.parsejson("earnest_deposit_type is required.", "", status=403))
                    
                    if "highest_best_format" in data and data['highest_best_format'] != "":
                        highest_best_format = int(data['highest_best_format'])
                    else:
                        return Response(response.parsejson("highest_best_format is required.", "", status=403))

                if "status" in data and data['status'] != "":
                    status = int(data['status'])
                else:
                    data['status'] = 2
                if property_asset != 1:
                    if "property_opening_dates" in data and type(data['property_opening_dates']) == list and len(data['property_opening_dates']) > 0:
                        property_opening_dates = data['property_opening_dates']
                    else:
                        return Response(response.parsejson("property_opening_dates is required.", "", status=403))

                if "property_auction_data" in data and type(data["property_auction_data"]) == dict and len(data["property_auction_data"]) > 0:
                    property_auction_data = data["property_auction_data"]
                    if "auction_status" in property_auction_data and property_auction_data["auction_status"] != "":
                        auction_status = int(property_auction_data["auction_status"])
                    else:
                        return Response(response.parsejson("property_auction_data->auction_status is required.", "", status=403))

                    if sale_by_type == 7:
                        start_price = None
                        if required_all == 1:
                            if "start_price" in property_auction_data and property_auction_data['start_price'] != "":
                                start_price = property_auction_data['start_price']
                            else:
                                if not un_priced:
                                    return Response(response.parsejson("property_auction_data->start_price is required.", "", status=403))
                    else:
                        if "start_price" in property_auction_data and property_auction_data['start_price'] != "":
                            start_price = property_auction_data['start_price']
                        else:
                            return Response(response.parsejson("property_auction_data->start_price is required.", "", status=403))
                    if sale_by_type != 4:
                        if "start_date" in property_auction_data and property_auction_data['start_date'] != "":
                            start_date = property_auction_data['start_date']
                        else:
                            return Response(response.parsejson("property_auction_data->start_date is required.", "", status=403))

                        if "end_date" in property_auction_data and property_auction_data['end_date'] != "":
                            end_date = property_auction_data['end_date']
                        else:
                            return Response(response.parsejson("property_auction_data->end_date is required.", "", status=403))
                    if sale_by_type == 1:
                        if "bid_increments" in property_auction_data and property_auction_data['bid_increments'] != "":
                            bid_increments = property_auction_data['bid_increments']
                        else:
                            return Response(response.parsejson("property_auction_data->bid_increments is required.", "", status=403))
                    if sale_by_type == 7:
                        if "offer_amount" in property_auction_data and property_auction_data['offer_amount'] != "":
                            offer_amount = property_auction_data['offer_amount']
                        else:
                            return Response(response.parsejson("property_auction_data->offer_amount is required.", "", status=403))

                    if sale_by_type != 2:
                        if "reserve_amount" in property_auction_data and property_auction_data['reserve_amount'] != "" and property_auction_data['reserve_amount'] is not None:
                            reserve_amount = property_auction_data['reserve_amount']
                            if float(start_price) > float(reserve_amount):
                                return Response(response.parsejson("reserve_amount should be greater than start_price.", "", status=403))

                    if sale_by_type == 2:
                        if "bid_increments" in property_auction_data and property_auction_data['bid_increments'] != "":
                            bid_increments = property_auction_data['bid_increments']
                        else:
                            return Response(response.parsejson("property_auction_data->bid_increments is required.", "", status=403))

                        if "insider_price_decrease" in property_auction_data and property_auction_data['insider_price_decrease'] != "":
                            insider_price_decrease = property_auction_data['insider_price_decrease']
                        else:
                            return Response(response.parsejson("property_auction_data->insider_price_decrease is required.", "", status=403))

                        if "dutch_time" in property_auction_data and property_auction_data['dutch_time'] != "":
                            dutch_time = property_auction_data['dutch_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_time is required.", "", status=403))

                        if "start_date" in property_auction_data and property_auction_data['start_date'] != "":
                            start_date = property_auction_data['start_date']
                        else:
                            return Response(response.parsejson("property_auction_data->start_date is required.", "", status=403))

                        if "dutch_end_time" in property_auction_data and property_auction_data['dutch_end_time'] != "":
                            dutch_end_time = property_auction_data['dutch_end_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_end_time is required.", "", status=403))

                        if "dutch_pause_time" in property_auction_data and property_auction_data['dutch_pause_time'] != "":
                            dutch_pause_time = property_auction_data['dutch_pause_time']
                        else:
                            return Response(response.parsejson("property_auction_data->dutch_pause_time is required.", "", status=403))

                        if "sealed_time" in property_auction_data and property_auction_data['sealed_time'] != "":
                            sealed_time = property_auction_data['sealed_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_time is required.", "", status=403))

                        if "sealed_start_time" in property_auction_data and property_auction_data['sealed_start_time'] != "":
                            sealed_start_time = property_auction_data['sealed_start_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_start_time is required.", "", status=403))

                        if "sealed_end_time" in property_auction_data and property_auction_data['sealed_end_time'] != "":
                            sealed_end_time = property_auction_data['sealed_end_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_end_time is required.", "", status=403))

                        if "sealed_pause_time" in property_auction_data and property_auction_data['sealed_pause_time'] != "":
                            sealed_pause_time = property_auction_data['sealed_pause_time']
                        else:
                            return Response(response.parsejson("property_auction_data->sealed_pause_time is required.", "", status=403))

                        if "english_time" in property_auction_data and property_auction_data['english_time'] != "":
                            english_time = property_auction_data['english_time']
                        else:
                            return Response(response.parsejson("property_auction_data->english_time is required.", "", status=403))

                        if "english_start_time" in property_auction_data and property_auction_data['english_start_time'] != "":
                            english_start_time = property_auction_data['english_start_time']
                        else:
                            return Response(response.parsejson("property_auction_data->english_start_time is required.", "", status=403))

                        # if "english_end_time" in property_auction_data and property_auction_data['english_end_time'] != "":
                        #     english_end_time = property_auction_data['english_end_time']
                        # else:
                        #     return Response(response.parsejson("property_auction_data->english_end_time is required.", "", status=403))
                else:
                    return Response(response.parsejson("property_auction_data is required.", "", status=403))

                if property_asset == 3:
                    if "beds" in data and data['beds'] != "":
                        beds = int(data['beds'])
                    else:
                        return Response(response.parsejson("beds is required.", "", status=403))

                    if "baths" in data and data['baths'] != "":
                        baths = int(data['baths'])
                    else:
                        return Response(response.parsejson("baths is required.", "", status=403))

                    if "year_built" in data and data['year_built'] != "":
                        year_built = int(data['year_built'])
                    else:
                        return Response(response.parsejson("year_built is required.", "", status=403))

                    if "square_footage" in data and data['square_footage'] != "":
                        square_footage = int(data['square_footage'])
                    else:
                        return Response(response.parsejson("square_footage is required.", "", status=403))
                elif property_asset == 2:
                    if "year_built" in data and data['year_built'] != "":
                        year_built = int(data['year_built'])
                    else:
                        return Response(response.parsejson("year_built is required.", "", status=403))

                    if "square_footage" in data and data['square_footage'] != "":
                        square_footage = int(data['square_footage'])
                    else:
                        return Response(response.parsejson("square_footage is required.", "", status=403))
                data["create_step"] = 1
                # data["status_id"] = 1
                data["title"] = "testing"
                serializer = AddPropertySerializer(property_id, data=data)
                if serializer.is_valid():
                    proeprty_data = serializer.save()
                    property_id = proeprty_data.id
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                # ----------------------Property Auction---------------------
                if "property_auction_data" in data and type(data["property_auction_data"]) == dict and len(data["property_auction_data"]) > 0:
                    property_auction_data = data["property_auction_data"]
                    property_auction = PropertyAuction.objects.filter(property=property_id).first()
                    if property_auction is None:
                        property_auction = PropertyAuction()
                        property_auction.property_id = property_id
                    property_auction.start_date = property_auction_data['start_date']
                    property_auction.end_date = property_auction_data['end_date'] if "end_date" in property_auction_data else None
                    # property_auction.bid_increments = property_auction_data['bid_increments']
                    property_auction.bid_increments = property_auction_data['bid_increments'] if "bid_increments" in property_auction_data and property_auction_data['bid_increments'] is not None and property_auction_data['bid_increments'] != "" else None
                    property_auction.reserve_amount = property_auction_data['reserve_amount'] if "reserve_amount" in property_auction_data and property_auction_data['reserve_amount'] is not None and property_auction_data['reserve_amount'] != "" else None
                    property_auction.time_zone_id = property_auction_data['time_zone']
                    # property_auction.start_price = property_auction_data['start_price']
                    property_auction.bid_increments = property_auction_data['start_price'] if "start_price" in property_auction_data and property_auction_data['start_price'] is not None and property_auction_data['start_price'] != "" else None
                    # property_auction.insider_decreased_price = property_auction_data['start_price']
                    property_auction.insider_decreased_price = property_auction_data['start_price'] if "start_price" in property_auction_data and property_auction_data['start_price'] is not None and property_auction_data['start_price'] != "" else None
                    property_auction.status_id = property_auction_data['auction_status']
                    property_auction.offer_amount = property_auction_data['offer_amount'] if "offer_amount" in property_auction_data else None
                    property_auction.auction_id = sale_by_type
                    property_auction.domain_id = site_id
                    property_auction.un_priced = un_priced
                    property_auction.required_all = required_all
                    property_auction.insider_price_decrease = property_auction_data['insider_price_decrease'] if "insider_price_decrease" in property_auction_data else None
                    property_auction.dutch_time = int(property_auction_data['dutch_time']) if "dutch_time" in property_auction_data else None
                    property_auction.dutch_end_time = property_auction_data['dutch_end_time'] if "dutch_end_time" in property_auction_data else None
                    property_auction.dutch_pause_time = int(property_auction_data['dutch_pause_time']) if "dutch_pause_time" in property_auction_data else None
                    property_auction.sealed_time = int(property_auction_data['sealed_time']) if "sealed_time" in property_auction_data else None
                    property_auction.sealed_start_time = property_auction_data['sealed_start_time'] if "sealed_start_time" in property_auction_data else None
                    property_auction.sealed_end_time = property_auction_data['sealed_end_time'] if "sealed_end_time" in property_auction_data else None
                    property_auction.sealed_pause_time = int(property_auction_data['sealed_pause_time']) if "sealed_pause_time" in property_auction_data else None
                    property_auction.english_time = int(property_auction_data['english_time']) if "english_time" in property_auction_data else None
                    property_auction.english_start_time = property_auction_data['english_start_time'] if "english_start_time" in property_auction_data else None
                    # property_auction.english_end_time = property_auction_data['english_end_time'] if "english_end_time" in property_auction_data else None
                    property_auction.save()
                # ----------------------Property Subtype---------------------
                if "property_subtype" in data and type(data["property_subtype"]) == list:
                    property_subtype = data["property_subtype"]
                    PropertySubtype.objects.filter(property=property_id).delete()
                    for subtype in property_subtype:
                        property_subtype = PropertySubtype()
                        property_subtype.property_id = property_id
                        property_subtype.subtype_id = subtype
                        property_subtype.save()

                # ----------------------Terms Accepted---------------------
                if "terms_accepted" in data and type(data["terms_accepted"]) == list:
                    terms_accepted = data["terms_accepted"]
                    PropertyTermAccepted.objects.filter(property=property_id).delete()
                    for terms in terms_accepted:
                        property_term_accepted = PropertyTermAccepted()
                        property_term_accepted.property_id = property_id
                        property_term_accepted.term_accepted_id = terms
                        property_term_accepted.save()

                # ----------------------Occupied By---------------------
                if "occupied_by" in data and type(data["occupied_by"]) == list:
                    occupied_by = data["occupied_by"]
                    PropertyOccupiedBy.objects.filter(property=property_id).delete()
                    for occupied in occupied_by:
                        property_occupied_by = PropertyOccupiedBy()
                        property_occupied_by.property_id = property_id
                        property_occupied_by.occupied_by_id = occupied
                        property_occupied_by.save()

                # ----------------------Ownership---------------------
                if "ownership" in data and type(data["ownership"]) == list:
                    ownership = data["ownership"]
                    PropertyOwnership.objects.filter(property=property_id).delete()
                    for owner in ownership:
                        property_ownership = PropertyOwnership()
                        property_ownership.property_id = property_id
                        property_ownership.ownership_id = owner
                        property_ownership.save()

                # ----------------------Possession---------------------
                if "possession" in data and type(data["possession"]) == list:
                    possession = data["possession"]
                    PropertyPossession.objects.filter(property=property_id).delete()
                    for pos in possession:
                        property_possession = PropertyPossession()
                        property_possession.property_id = property_id
                        property_possession.possession_id = pos
                        property_possession.save()

                # ----------------------Style---------------------
                if "style" in data and type(data["style"]) == list:
                    style = data["style"]
                    PropertyStyle.objects.filter(property=property_id).delete()
                    for st in style:
                        property_style = PropertyStyle()
                        property_style.property_id = property_id
                        property_style.style_id = st
                        property_style.save()

                # ----------------------Cooling---------------------
                if "cooling" in data and type(data["cooling"]) == list:
                    cooling = data["cooling"]
                    PropertyCooling.objects.filter(property=property_id).delete()
                    for cool in cooling:
                        property_cooling = PropertyCooling()
                        property_cooling.property_id = property_id
                        property_cooling.cooling_id = cool
                        property_cooling.save()

                # ----------------------Stories---------------------
                if "stories" in data and type(data["stories"]) == list:
                    stories = data["stories"]
                    PropertyStories.objects.filter(property=property_id).delete()
                    for story in stories:
                        property_stories = PropertyStories()
                        property_stories.property_id = property_id
                        property_stories.stories_id = story
                        property_stories.save()

                # ----------------------HeatingStories---------------------
                if "heating" in data and type(data["heating"]) == list:
                    heating = data["heating"]
                    PropertyHeating.objects.filter(property=property_id).delete()
                    for heat in heating:
                        property_heating = PropertyHeating()
                        property_heating.property_id = property_id
                        property_heating.heating_id = heat
                        property_heating.save()

                # ----------------------Electric---------------------
                if "electric" in data and type(data["electric"]) == list:
                    electric = data["electric"]
                    PropertyElectric.objects.filter(property=property_id).delete()
                    for ele in electric:
                        property_electric = PropertyElectric()
                        property_electric.property_id = property_id
                        property_electric.electric_id = ele
                        property_electric.save()

                # ----------------------Gas---------------------
                if "gas" in data and type(data["gas"]) == list:
                    gas = data["gas"]
                    PropertyGas.objects.filter(property=property_id).delete()
                    for g in gas:
                        property_gas = PropertyGas()
                        property_gas.property_id = property_id
                        property_gas.gas_id = g
                        property_gas.save()

                # ----------------------Recent Updates---------------------
                if "recent_updates" in data and type(data["recent_updates"]) == list:
                    recent_updates = data["recent_updates"]
                    PropertyRecentUpdates.objects.filter(property=property_id).delete()
                    for updates in recent_updates:
                        property_recent_updates = PropertyRecentUpdates()
                        property_recent_updates.property_id = property_id
                        property_recent_updates.recent_updates_id = updates
                        property_recent_updates.save()

                # ----------------------Water---------------------
                if "water" in data and type(data["water"]) == list:
                    water = data["water"]
                    PropertyWater.objects.filter(property=property_id).delete()
                    for wa in water:
                        property_water = PropertyWater()
                        property_water.property_id = property_id
                        property_water.water_id = wa
                        property_water.save()

                # ----------------------Security Features---------------------
                if "security_features" in data and type(data["security_features"]) == list:
                    security_features = data["security_features"]
                    PropertySecurityFeatures.objects.filter(property=property_id).delete()
                    for security in security_features:
                        property_security_features = PropertySecurityFeatures()
                        property_security_features.property_id = property_id
                        property_security_features.security_features_id = security
                        property_security_features.save()

                # ----------------------Sewer---------------------
                if "sewer" in data and type(data["sewer"]) == list:
                    sewer = data["sewer"]
                    PropertySewer.objects.filter(property=property_id).delete()
                    for se in sewer:
                        property_sewer = PropertySewer()
                        property_sewer.property_id = property_id
                        property_sewer.sewer_id = se
                        property_sewer.save()

                # ----------------------Tax Exemptions---------------------
                if "tax_exemptions" in data and type(data["tax_exemptions"]) == list:
                    tax_exemptions = data["tax_exemptions"]
                    PropertyTaxExemptions.objects.filter(property=property_id).delete()
                    for tax in tax_exemptions:
                        property_tax_exemptions = PropertyTaxExemptions()
                        property_tax_exemptions.property_id = property_id
                        property_tax_exemptions.tax_exemptions_id = tax
                        property_tax_exemptions.save()

                # ----------------------Zoning---------------------
                if "zoning" in data and type(data["zoning"]) == list:
                    zoning = data["zoning"]
                    PropertyZoning.objects.filter(property=property_id).delete()
                    for zo in zoning:
                        property_zoning = PropertyZoning()
                        property_zoning.property_id = property_id
                        property_zoning.zoning_id = zo
                        property_zoning.save()

                # ----------------------Hoa Amenities---------------------
                if "hoa_amenities" in data and type(data["hoa_amenities"]) == list:
                    hoa_amenities = data["hoa_amenities"]
                    PropertyAmenities.objects.filter(property=property_id).delete()
                    for hoa in hoa_amenities:
                        property_amenities = PropertyAmenities()
                        property_amenities.property_id = property_id
                        property_amenities.amenities_id = hoa
                        property_amenities.save()

                # ----------------------Kitchen Features---------------------
                if "kitchen_features" in data and type(data["kitchen_features"]) == list:
                    kitchen_features = data["kitchen_features"]
                    PropertyKitchenFeatures.objects.filter(property=property_id).delete()
                    for kitchen in kitchen_features:
                        property_kitchen_features = PropertyKitchenFeatures()
                        property_kitchen_features.property_id = property_id
                        property_kitchen_features.kitchen_features_id = kitchen
                        property_kitchen_features.save()

                # ----------------------Appliances---------------------
                if "appliances" in data and type(data["appliances"]) == list:
                    appliances = data["appliances"]
                    PropertyAppliances.objects.filter(property=property_id).delete()
                    for apl in appliances:
                        property_appliances = PropertyAppliances()
                        property_appliances.property_id = property_id
                        property_appliances.appliances_id = apl
                        property_appliances.save()

                # ----------------------Flooring---------------------
                if "flooring" in data and type(data["flooring"]) == list:
                    flooring = data["flooring"]
                    PropertyFlooring.objects.filter(property=property_id).delete()
                    for floor in flooring:
                        property_flooring = PropertyFlooring()
                        property_flooring.property_id = property_id
                        property_flooring.flooring_id = floor
                        property_flooring.save()

                # ----------------------Windows---------------------
                if "windows" in data and type(data["windows"]) == list:
                    windows = data["windows"]
                    PropertyWindows.objects.filter(property=property_id).delete()
                    for window in windows:
                        property_windows = PropertyWindows()
                        property_windows.property_id = property_id
                        property_windows.windows_id = window
                        property_windows.save()

                # ----------------------Bedroom Features---------------------
                if "bedroom_features" in data and type(data["bedroom_features"]) == list:
                    bedroom_features = data["bedroom_features"]
                    PropertyBedroomFeatures.objects.filter(property=property_id).delete()
                    for bedroom in bedroom_features:
                        property_bedroom_features = PropertyBedroomFeatures()
                        property_bedroom_features.property_id = property_id
                        property_bedroom_features.bedroom_features_id = bedroom
                        property_bedroom_features.save()

                # ----------------------Other Rooms---------------------
                if "other_rooms" in data and type(data["other_rooms"]) == list:
                    other_rooms = data["other_rooms"]
                    PropertyOtherRooms.objects.filter(property=property_id).delete()
                    for other in other_rooms:
                        property_other_rooms = PropertyOtherRooms()
                        property_other_rooms.property_id = property_id
                        property_other_rooms.other_rooms_id = other
                        property_other_rooms.save()

                # ----------------------Bathroom Features---------------------
                if "bathroom_features" in data and type(data["bathroom_features"]) == list:
                    bathroom_features = data["bathroom_features"]
                    PropertyBathroomFeatures.objects.filter(property=property_id).delete()
                    for bathroom in bathroom_features:
                        property_bathroom_features = PropertyBathroomFeatures()
                        property_bathroom_features.property_id = property_id
                        property_bathroom_features.bathroom_features_id = bathroom
                        property_bathroom_features.save()
                # ----------------------Other Features---------------------
                if "other_features" in data and type(data["other_features"]) == list:
                    other_features = data["other_features"]
                    PropertyOtherFeatures.objects.filter(property=property_id).delete()
                    for other in other_features:
                        property_other_features = PropertyOtherFeatures()
                        property_other_features.property_id = property_id
                        property_other_features.other_features_id = other
                        property_other_features.save()

                # ----------------------Master Bedroom Features---------------------
                if "master_bedroom_features" in data and type(data["master_bedroom_features"]) == list:
                    master_bedroom_features = data["master_bedroom_features"]
                    PropertyMasterBedroomFeatures.objects.filter(property=property_id).delete()
                    for master_bedroom in master_bedroom_features:
                        property_master_bedroom_features = PropertyMasterBedroomFeatures()
                        property_master_bedroom_features.property_id = property_id
                        property_master_bedroom_features.master_bedroom_features_id = master_bedroom
                        property_master_bedroom_features.save()

                # ----------------------Fireplace Type---------------------
                if "fireplace_type" in data and type(data["fireplace_type"]) == list:
                    fireplace_type = data["fireplace_type"]
                    PropertyFireplaceType.objects.filter(property=property_id).delete()
                    for fireplace in fireplace_type:
                        property_fireplace_type = PropertyFireplaceType()
                        property_fireplace_type.property_id = property_id
                        property_fireplace_type.fireplace_type_id = fireplace
                        property_fireplace_type.save()

                # ----------------------Basement Features---------------------
                if "basement_features" in data and type(data["basement_features"]) == list:
                    basement_features = data["basement_features"]
                    PropertyBasementFeatures.objects.filter(property=property_id).delete()
                    for basement in basement_features:
                        property_basement_features = PropertyBasementFeatures()
                        property_basement_features.property_id = property_id
                        property_basement_features.basement_features_id = basement
                        property_basement_features.save()

                # ----------------------Handicap Amenities---------------------
                if "handicap_amenities" in data and type(data["handicap_amenities"]) == list:
                    handicap_amenities = data["handicap_amenities"]
                    PropertyHandicapAmenities.objects.filter(property=property_id).delete()
                    for amenities in handicap_amenities:
                        property_handicap_amenities = PropertyHandicapAmenities()
                        property_handicap_amenities.property_id = property_id
                        property_handicap_amenities.handicap_amenities_id = amenities
                        property_handicap_amenities.save()

                # ----------------------Construction---------------------
                if "construction" in data and type(data["construction"]) == list:
                    construction = data["construction"]
                    PropertyConstruction.objects.filter(property=property_id).delete()
                    for cons in construction:
                        property_construction = PropertyConstruction()
                        property_construction.property_id = property_id
                        property_construction.construction_id = cons
                        property_construction.save()

                # ----------------------Garage Parking---------------------
                if "garage_parking" in data and type(data["garage_parking"]) == list:
                    garage_parking = data["garage_parking"]
                    PropertyGarageParking.objects.filter(property=property_id).delete()
                    for parking in garage_parking:
                        property_garage_parking = PropertyGarageParking()
                        property_garage_parking.property_id = property_id
                        property_garage_parking.garage_parking_id = parking
                        property_garage_parking.save()

                # ----------------------Exterior Features---------------------
                if "exterior_features" in data and type(data["exterior_features"]) == list:
                    exterior_features = data["exterior_features"]
                    PropertyExteriorFeatures.objects.filter(property=property_id).delete()
                    for exterior in exterior_features:
                        property_exterior_features = PropertyExteriorFeatures()
                        property_exterior_features.property_id = property_id
                        property_exterior_features.exterior_features_id = exterior
                        property_exterior_features.save()

                # ----------------------Garage Features---------------------
                if "garage_features" in data and type(data["garage_features"]) == list:
                    garage_features = data["garage_features"]
                    PropertyGarageFeatures.objects.filter(property=property_id).delete()
                    for garage in garage_features:
                        property_garage_features = PropertyGarageFeatures()
                        property_garage_features.property_id = property_id
                        property_garage_features.garage_features_id = garage
                        property_garage_features.save()

                # ----------------------Roof---------------------
                if "roof" in data and type(data["roof"]) == list:
                    roof = data["roof"]
                    PropertyRoof.objects.filter(property=property_id).delete()
                    for rf in roof:
                        property_roof = PropertyRoof()
                        property_roof.property_id = property_id
                        property_roof.roof_id = rf
                        property_roof.save()

                # ----------------------Outbuildings---------------------
                if "outbuildings" in data and type(data["outbuildings"]) == list:
                    outbuildings = data["outbuildings"]
                    PropertyOutbuildings.objects.filter(property=property_id).delete()
                    for buildings in outbuildings:
                        property_outbuildings = PropertyOutbuildings()
                        property_outbuildings.property_id = property_id
                        property_outbuildings.outbuildings_id = buildings
                        property_outbuildings.save()

                # ----------------------Foundation---------------------
                if "foundation" in data and type(data["foundation"]) == list:
                    foundation = data["foundation"]
                    PropertyFoundation.objects.filter(property=property_id).delete()
                    for fd in foundation:
                        property_foundation = PropertyFoundation()
                        property_foundation.property_id = property_id
                        property_foundation.foundation_id = fd
                        property_foundation.save()

                # ----------------------Location Features---------------------
                if "location_features" in data and type(data["location_features"]) == list:
                    location_features = data["location_features"]
                    PropertyLocationFeatures.objects.filter(property=property_id).delete()
                    for location in location_features:
                        property_location_features = PropertyLocationFeatures()
                        property_location_features.property_id = property_id
                        property_location_features.location_features_id = location
                        property_location_features.save()

                # ----------------------Fence---------------------
                if "fence" in data and type(data["fence"]) == list:
                    fence = data["fence"]
                    PropertyFence.objects.filter(property=property_id).delete()
                    for fnc in fence:
                        property_fence = PropertyFence()
                        property_fence.property_id = property_id
                        property_fence.fence_id = fnc
                        property_fence.save()

                # ----------------------Road Frontage---------------------
                if "road_frontage" in data and type(data["road_frontage"]) == list:
                    road_frontage = data["road_frontage"]
                    PropertyRoadFrontage.objects.filter(property=property_id).delete()
                    for frontage in road_frontage:
                        property_road_frontage = PropertyRoadFrontage()
                        property_road_frontage.property_id = property_id
                        property_road_frontage.road_frontage_id = frontage
                        property_road_frontage.save()

                # ----------------------Pool---------------------
                if "pool" in data and type(data["pool"]) == list:
                    pool = data["pool"]
                    PropertyPool.objects.filter(property=property_id).delete()
                    for pl in pool:
                        property_pool = PropertyPool()
                        property_pool.property_id = property_id
                        property_pool.pool_id = pl
                        property_pool.save()

                # ----------------------Property Faces---------------------
                if "property_faces" in data and type(data["property_faces"]) == list:
                    property_faces = data["property_faces"]
                    PropertyPropertyFaces.objects.filter(property=property_id).delete()
                    for faces in property_faces:
                        property_property_faces = PropertyPropertyFaces()
                        property_property_faces.property_id = property_id
                        property_property_faces.property_faces_id = faces
                        property_property_faces.save()

                # ----------------Commercial------------------

                # ----------------------Property Faces---------------------
                if "lease_type" in data and type(data["lease_type"]) == list:
                    lease_type = data["lease_type"]
                    PropertyLeaseType.objects.filter(property=property_id).delete()
                    for lease in lease_type:
                        property_lease_type = PropertyLeaseType()
                        property_lease_type.property_id = property_id
                        property_lease_type.lease_type_id = lease
                        property_lease_type.save()

                # ----------------------Tenant Pays---------------------
                if "tenant_pays" in data and type(data["tenant_pays"]) == list:
                    tenant_pays = data["tenant_pays"]
                    PropertyTenantPays.objects.filter(property=property_id).delete()
                    for tenant in tenant_pays:
                        property_tenant_pays = PropertyTenantPays()
                        property_tenant_pays.property_id = property_id
                        property_tenant_pays.tenant_pays_id = tenant
                        property_tenant_pays.save()

                # ----------------------Tenant Pays---------------------
                if "tenant_pays" in data and type(data["tenant_pays"]) == list:
                    tenant_pays = data["tenant_pays"]
                    PropertyTenantPays.objects.filter(property=property_id).delete()
                    for tenant in tenant_pays:
                        property_tenant_pays = PropertyTenantPays()
                        property_tenant_pays.property_id = property_id
                        property_tenant_pays.tenant_pays_id = tenant
                        property_tenant_pays.save()

                # ----------------------Inclusions---------------------
                if "inclusions" in data and type(data["inclusions"]) == list:
                    inclusions = data["inclusions"]
                    PropertyInclusions.objects.filter(property=property_id).delete()
                    for incl in inclusions:
                        property_inclusions = PropertyInclusions()
                        property_inclusions.property_id = property_id
                        property_inclusions.inclusions_id = incl
                        property_inclusions.save()

                # ----------------------Building Class---------------------
                if "building_class" in data and type(data["building_class"]) == list:
                    building_class = data["building_class"]
                    PropertyBuildingClass.objects.filter(property=property_id).delete()
                    for building in building_class:
                        property_building_class = PropertyBuildingClass()
                        property_building_class.property_id = property_id
                        property_building_class.building_class_id = building
                        property_building_class.save()

                # ----------------------Interior Features---------------------
                if "interior_features" in data and type(data["interior_features"]) == list:
                    interior_features = data["interior_features"]
                    PropertyInteriorFeatures.objects.filter(property=property_id).delete()
                    for interior in interior_features:
                        property_interior_features = PropertyInteriorFeatures()
                        property_interior_features.property_id = property_id
                        property_interior_features.interior_features_id = interior
                        property_interior_features.save()

                # ------------------Land-----------------
                # ----------------------Mineral Rights---------------------
                if "mineral_rights" in data and type(data["mineral_rights"]) == list:
                    mineral_rights = data["mineral_rights"]
                    PropertyMineralRights.objects.filter(property=property_id).delete()
                    for mineral in mineral_rights:
                        property_mineral_rights = PropertyMineralRights()
                        property_mineral_rights.property_id = property_id
                        property_mineral_rights.mineral_rights_id = mineral
                        property_mineral_rights.save()

                # ----------------------Easements---------------------
                if "easements" in data and type(data["easements"]) == list:
                    easements = data["easements"]
                    PropertyEasements.objects.filter(property=property_id).delete()
                    for eas in easements:
                        property_easements = PropertyEasements()
                        property_easements.property_id = property_id
                        property_easements.easements_id = eas
                        property_easements.save()

                # ----------------------Survey---------------------
                if "survey" in data and type(data["survey"]) == list:
                    survey = data["survey"]
                    PropertySurvey.objects.filter(property=property_id).delete()
                    for sur in survey:
                        property_survey = PropertySurvey()
                        property_survey.property_id = property_id
                        property_survey.survey_id = sur
                        property_survey.save()

                # ----------------------Utilities---------------------
                if "utilities" in data and type(data["utilities"]) == list:
                    utilities = data["utilities"]
                    PropertyUtilities.objects.filter(property=property_id).delete()
                    for uti in utilities:
                        property_utilities = PropertyUtilities()
                        property_utilities.property_id = property_id
                        property_utilities.utilities_id = uti
                        property_utilities.save()

                # ----------------------Improvements---------------------
                if "improvements" in data and type(data["improvements"]) == list:
                    improvements = data["improvements"]
                    PropertyImprovements.objects.filter(property=property_id).delete()
                    for imp in improvements:
                        property_improvements = PropertyImprovements()
                        property_improvements.property_id = property_id
                        property_improvements.improvements_id = imp
                        property_improvements.save()

                # ----------------------Topography---------------------
                if "topography" in data and type(data["topography"]) == list:
                    topography = data["topography"]
                    PropertyTopography.objects.filter(property=property_id).delete()
                    for top in topography:
                        property_topography = PropertyTopography()
                        property_topography.property_id = property_id
                        property_topography.topography_id = top
                        property_topography.save()

                # ----------------------Wildlife---------------------
                if "wildlife" in data and type(data["wildlife"]) == list:
                    wildlife = data["wildlife"]
                    PropertyWildlife.objects.filter(property=property_id).delete()
                    for wild in wildlife:
                        property_wildlife = PropertyWildlife()
                        property_wildlife.property_id = property_id
                        property_wildlife.wildlife_id = wild
                        property_wildlife.save()

                # ----------------------Fish---------------------
                if "fish" in data and type(data["fish"]) == list:
                    fish = data["fish"]
                    PropertyFish.objects.filter(property=property_id).delete()
                    for fi in fish:
                        property_fish = PropertyFish()
                        property_fish.property_id = property_id
                        property_fish.fish_id = fi
                        property_fish.save()

                # ----------------------Irrigation System---------------------
                if "irrigation_system" in data and type(data["irrigation_system"]) == list:
                    irrigation_system = data["irrigation_system"]
                    PropertyIrrigationSystem.objects.filter(property=property_id).delete()
                    for irrigation in irrigation_system:
                        property_irrigation_system = PropertyIrrigationSystem()
                        property_irrigation_system.property_id = property_id
                        property_irrigation_system.irrigation_system_id = irrigation
                        property_irrigation_system.save()

                # ----------------------Recreation---------------------
                if "recreation" in data and type(data["recreation"]) == list:
                    recreation = data["recreation"]
                    PropertyRecreation.objects.filter(property=property_id).delete()
                    for rec in recreation:
                        property_recreation = PropertyRecreation()
                        property_recreation.property_id = property_id
                        property_recreation.recreation_id = rec
                        property_recreation.save()

                # ----------------------Property opening date---------------------
                if property_asset != 1:
                    if "property_opening_dates" in data and type(data["property_opening_dates"]) == list:
                        property_opening_dates = data["property_opening_dates"]
                        PropertyOpening.objects.filter(property=property_id).delete()
                        for dates in property_opening_dates:
                            property_opening = PropertyOpening()
                            property_opening.domain_id = site_id
                            property_opening.property_id = property_id
                            property_opening.opening_start_date = dates['start_date']
                            property_opening.opening_end_date = dates['end_date']
                            property_opening.status_id = 1
                            property_opening.save()

            elif step == 2:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "is_map_view" in data and data["is_map_view"] != "":
                    is_map_view = data["is_map_view"]
                else:
                    return Response(response.parsejson("is_map_view is required.", "", status=403))

                if "is_street_view" in data and data["is_street_view"] != "":
                    is_street_view = data["is_street_view"]
                else:
                    return Response(response.parsejson("is_street_view is required.", "", status=403))

                if "is_arial_view" in data and data["is_arial_view"] != "":
                    is_arial_view = data["is_arial_view"]
                else:
                    return Response(response.parsejson("is_arial_view is required.", "", status=403))
                map_url = None
                if "map_url" in data and data["map_url"] != "":
                    map_url = data["map_url"]
                # else:
                #     return Response(response.parsejson("map_url is required.", "", status=403))

                latitude = None
                if "latitude" in data and data["latitude"] != "":
                    latitude = data["latitude"]

                longitude = None
                if "longitude" in data and data["longitude"] != "":
                    longitude = data["longitude"]

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.is_map_view = is_map_view
                property_listing.is_street_view = is_street_view
                property_listing.is_arial_view = is_arial_view
                property_listing.create_step = 2
                property_listing.map_url = map_url
                if latitude is not None:
                    property_listing.latitude = latitude
                if longitude is not None:
                    property_listing.longitude = longitude
                property_listing.save()
            elif step == 3:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "property_pic" in data and type(data["property_pic"]) == list and len(data["property_pic"]) > 0:
                    property_pic = data["property_pic"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=1).delete()
                    for pic in property_pic:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = pic
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 1
                        property_uploads.status_id = 1
                        property_uploads.save()

                if "property_video" in data and type(data["property_video"]) == list and len(data["property_video"]) > 0:
                    property_video = data["property_video"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=2).delete()
                    for video in property_video:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = video
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 2
                        property_uploads.status_id = 1
                        property_uploads.save()

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.create_step = 3
                property_listing.save()
            elif step == 4:
                if property_id is None:
                    return Response(response.parsejson("property_id is required.", "", status=403))
                property_id = property_id.id
                if "property_documents" in data and type(data["property_documents"]) == list and len(data["property_documents"]) > 0:
                    property_documents = data["property_documents"]
                    PropertyUploads.objects.filter(property=property_id, upload_type=3).delete()
                    for documents in property_documents:
                        property_uploads = PropertyUploads()
                        property_uploads.upload_id = documents
                        property_uploads.property_id = property_id
                        property_uploads.upload_type = 3
                        property_uploads.status_id = 1
                        property_uploads.save()

                property_listing = PropertyListing.objects.get(id=property_id)
                property_listing.create_step = 4
                property_listing.save()
            all_data = {"property_id": property_id}
            try:
                if not check_update:
                    # Send email to agent and broker
                    broker_data = Users.objects.get(site_id=proeprty_data.domain_id)
                    agent_data = proeprty_data.agent
                    super_admin_data = Users.objects.get(id=admin_id)
                    property_user_name = agent_data.first_name
                    agent_email = agent_data.email
                    auction_type = proeprty_data.sale_by_type.auction_type
                    auction_data = PropertyAuction.objects.get(property=property_id)
                    start_price = auction_data.start_price
                    upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                    web_url = settings.FRONT_BASE_URL
                    image_url = web_url+'/static/admin/images/property-default-img.png'
                    if upload is not None:
                        image = upload.upload.doc_file_name
                        bucket_name = upload.upload.bucket_name
                        image_url = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
                    subdomain_url = settings.SUBDOMAIN_URL
                    domain_name = network.domain_name
                    domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/"
                    notif_type = 2
                    if proeprty_data.sale_by_type_id == 7:
                        notif_type = 6
                        domain_url = domain_url + "?auction_type=highest%20offer"
                    elif proeprty_data.sale_by_type_id == 4:
                        notif_type = 4
                        domain_url = domain_url + "?auction_type=traditional%20offer"
                    elif proeprty_data.sale_by_type_id == 6:
                        notif_type = 7
                        domain_url = domain_url + "?auction_type=live%20offer"
                    domain_name_url = subdomain_url.replace("###", domain_name)
                    template_data = {"domain_id": proeprty_data.domain_id, "slug": "add_listing_super_admin"}
                    prop_name = proeprty_data.address_one if proeprty_data.address_one else proeprty_data.id
                    extra_data = {
                        'property_user_name': broker_data.first_name,
                        'domain_name': domain_name_url,
                        'name': super_admin_data.first_name,
                        'email': super_admin_data.email,
                        'phone':  phone_format(super_admin_data.phone_no),
                        'property_image': image_url,
                        'property_address': proeprty_data.address_one,
                        'property_city': proeprty_data.city,
                        'property_state': proeprty_data.state.state_name,
                        'auction_type': auction_type,
                        'asset_type': proeprty_data.property_asset.name,
                        'starting_price': "$" + number_format(start_price) if not auction_data.un_priced else 'Unpriced',
                        'starting_bid_offer': 'Starting Bid' if proeprty_data.sale_by_type_id in [1, 6] else "Asking Price",
                        'dashboard_link': domain_url,
                        'domain_id': proeprty_data.domain_id
                    }

                    # Email for broker
                    compose_email(to_email=[broker_data.email], template_data=template_data, extra_data=extra_data)

                    #  add notif to broker
                    content = "A new listing is created on your domain! <span>[" + prop_name + "]</span>"
                    add_notification(
                        proeprty_data.domain_id,
                        "Create Listing",
                        content,
                        user_id=broker_data.id,
                        added_by=admin_id,
                        notification_for=2,
                        property_id=proeprty_data.id,
                        notification_type=notif_type
                        )

                    # identify agent
                    if broker_data.id != proeprty_data.agent_id:
                        extra_data['property_user_name'] = property_user_name
                        # email for agent
                        compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                        #  add notif to agent
                        content = "A new listing is created for you! <span>[" + prop_name + "]</span>"
                        add_notification(
                            proeprty_data.domain_id,
                            "Create Listing",
                            content,
                            user_id=proeprty_data.agent_id,
                            added_by=admin_id,
                            notification_for=2,
                            property_id=proeprty_data.id,
                            notification_type=notif_type
                            )
            except Exception as e:
                pass

            return Response(response.parsejson("Property added/updated successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPropertyDetailApiView(APIView):
    """
    Admin property detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            # if "step_id" in data and data['step_id'] != "":
            #     step_id = int(data['step_id'])
            # else:
            #     return Response(response.parsejson("step_id is required", "", status=403))
            property_listing = PropertyListing.objects.get(id=property_id)
            # if step_id == 1:
            #     serializer = AdminPropertyDetailStepOneSerializer(property_listing)
            # elif step_id == 2:
            #     serializer = AdminPropertyDetailStepTwoSerializer(property_listing)
            # elif step_id == 3:
            #     serializer = AdminPropertyDetailStepThreeSerializer(property_listing)
            # elif step_id == 4:
            #     serializer = AdminPropertyDetailStepFourSerializer(property_listing)
            response_data = {
                'step_1': AdminPropertyDetailStepOneSerializer(property_listing).data,
                'step_2': AdminPropertyDetailStepTwoSerializer(property_listing).data,
                'step_3': AdminPropertyDetailStepThreeSerializer(property_listing).data,
                'step_4': AdminPropertyDetailStepFourSerializer(property_listing).data
            }

            return Response(response.parsejson("Fetch Data.", response_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontPropertyListingApiView(APIView):
    """
    Front property listing
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            if "filter" in data and data["filter"] == "recent_sold_listing":
                status = 9
            else:
                status = 1

            property_listing = PropertyListing.objects.filter(domain=site_id, is_approved=1, status=status)

            # -----------------Filter-------------------
            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_listing = property_listing.filter(Q(sale_by_type=auction_id))

            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_listing = property_listing.filter(Q(agent=agent_id))

            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                property_listing = property_listing.filter(Q(property_asset=asset_id))

            if "status" in data and data["status"] != "":
                status = int(data["status"])
                property_listing = property_listing.filter(Q(status=status))

            if "filter" in data and data["filter"] == "auctions_listing":
                property_listing = property_listing.filter(Q(property_auction__start_date__isnull=False) & Q(property_auction__end_date__isnull=False)).exclude(sale_by_type__in=[4, 7])
            elif "filter" in data and data["filter"] == "new_listing":
                min_dt = timezone.now() - timedelta(hours=720)
                # max_dt = timezone.now()
                property_listing = property_listing.filter(added_on__gte=min_dt)
            elif "filter" in data and data["filter"] == "traditional_listing":
                property_listing = property_listing.filter(sale_by_type=4)
            elif "filter" in data and data["filter"] == "recent_sold_listing":
                # min_dt = timezone.now() - timedelta(hours=720)
                # max_dt = timezone.now()
                # property_listing = property_listing.filter(date_sold__gte=min_dt)
                pass
            elif "filter" in data and data["filter"] == "featured":
                property_listing = property_listing.filter(is_featured=1)

            if "filter_asset_type" in data and data["filter_asset_type"] != "":
                property_listing = property_listing.filter(property_asset=int(data["filter_asset_type"]))
            if "filter_property_type" in data and data["filter_property_type"] != "":
                    property_listing = property_listing.filter(property_type=int(data["filter_property_type"])) 
            if "filter_auction_type" in data and data["filter_auction_type"] != "":
                property_listing = property_listing.filter(sale_by_type=int(data["filter_auction_type"]))
            if "filter_beds" in data and data["filter_beds"] != "":
                property_listing = property_listing.filter(beds__gt=int(data["filter_beds"]))
            if "filter_baths" in data and data["filter_baths"] != "":
                property_listing = property_listing.filter(baths__gt=int(data["filter_baths"]))
            if "filter_mls_property" in data and data["filter_mls_property"] != "":
                property_listing = property_listing.filter(idx_property_id__icontains=data["filter_mls_property"])

            if "filter_min_price" in data and data["filter_min_price"] != "" and "filter_max_price" in data and data["filter_max_price"] != "":
                property_listing = property_listing.filter(Q(property_auction__start_price__gte=data["filter_min_price"]) & Q(property_auction__start_price__lte=data["filter_max_price"]))
            elif "filter_min_price" in data and data["filter_min_price"] != "" and "filter_max_price" in data and data["filter_max_price"] == "":
                property_listing = property_listing.filter(Q(property_auction__start_price__gte=data["filter_min_price"]))
            elif "filter_min_price" in data and data["filter_min_price"] == "" and "filter_max_price" in data and data["filter_max_price"] != "":
                property_listing = property_listing.filter(Q(property_auction__start_price__lte=data["filter_max_price"]))
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    property_listing = property_listing.filter(Q(id=search) | Q(postal_code__icontains=search) | Q(idx_property_id__icontains=search))
                else:
                    property_listing = property_listing.filter(Q(city__icontains=search) |
                                                               Q(state__state_name__icontains=search) |
                                                               Q(address_one__icontains=search) |
                                                               Q(postal_code__icontains=search) |
                                                               Q(property_asset__name__icontains=search) |
                                                               Q(sale_by_type__auction_type__icontains=search) |
                                                               Q(idx_property_id__icontains=search))

            # -----------------Sort------------------
            # if "short_by" in data and data["short_by"] != "" and "sort_order" in data and data["sort_order"] != "":
            if "short_by" in data and data["short_by"] != "":
                if data["short_by"].lower() == "auction_start" and data["sort_order"].lower() == "asc":
                    property_listing = property_listing.order_by(F("property_auction__start_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "auction_start" and data["sort_order"].lower() == "desc":
                    property_listing = property_listing.order_by(F("property_auction__start_date").desc(nulls_last=True))
                elif data["short_by"].lower() == "auction_end" and data["sort_order"].lower() == "asc":
                    property_listing = property_listing.order_by(F("property_auction__end_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "auction_end" and data["sort_order"].lower() == "desc":
                    property_listing = property_listing.order_by(F("property_auction__end_date").desc(nulls_last=True))
                elif data["short_by"].lower() == "highest_price":
                    property_listing = property_listing.order_by(F("property_auction__start_price").desc(nulls_last=True))
                elif data["short_by"].lower() == "lowest_price":
                    property_listing = property_listing.order_by(F("property_auction__start_price").asc(nulls_last=True))
                elif data["short_by"].lower() == "page_default":
                    property_listing = property_listing.order_by(F("ordering").asc(nulls_last=True))
                elif data["short_by"].lower() == "ending_soonest":
                    property_listing = property_listing.order_by(F("property_auction__end_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "ending_latest":
                    property_listing = property_listing.order_by(F("property_auction__end_date").desc(nulls_last=True))
            else:
                property_listing = property_listing.order_by(F("ordering").asc(nulls_last=True))

            total = property_listing.count()
            property_listing = property_listing.only("id")[offset:limit]
            serializer = FrontPropertyListingSerializer(property_listing, many=True, context={"user_id": user_id})
            all_data = {"data": serializer.data, "total": total}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyDetailApiView(APIView):
    """
    Property detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            property_listing = PropertyListing.objects.get(id=property_id, domain=site_id)
            serializer = PropertyDetailSerializer(property_listing, context=user_id)
            return Response(response.parsejson("Fetch Data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyStatusChangeApiView(APIView):
    """
    Property status change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("You are not authentic user to update property.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                # Translators: This message appears when status is empty
                return Response(response.parsejson("status is required", "", status=403))

            PropertyListing.objects.filter(id=property_id, domain=site_id).update(status_id=status)
            return Response(response.parsejson("Status changed successfully..", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyApprovalChangeApiView(APIView):
    """
    Property approval change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("You are not authentic user to update property.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            if "is_approved" in data and data['is_approved'] != "":
                is_approved = data['is_approved']
            else:
                # Translators: This message appears when is_approved is empty
                return Response(response.parsejson("is_approved is required", "", status=403))

            PropertyListing.objects.filter(id=property_id, domain=site_id).update(is_approved=is_approved)
            try:
                #-------------Email--------------------
                if "is_approved" in data and int(data['is_approved']) == 1:
                    property_approved_status = 'approved'
                else:
                    property_approved_status = 'unapproved'
                property_detail = PropertyListing.objects.get(id=property_id)
                user_detail = Users.objects.get(id=property_detail.agent_id)
                property_user_name = user_detail.first_name
                agent_email = user_detail.email
                auction_type = property_detail.sale_by_type.auction_type
                auction_data = PropertyAuction.objects.get(property=property_id)
                start_price = auction_data.start_price
                upload = None
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name


                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/"
                notif_type = 2
                if property_detail.sale_by_type_id == 7:
                    domain_url = domain_url + "?auction_type=highest%20offer"
                    notif_type = 6
                elif property_detail.sale_by_type_id == 4:
                    notif_type = 4
                    domain_url = domain_url + "?auction_type=traditional%20offer"
                elif property_detail.sale_by_type_id == 6:
                    notif_type = 7
                    domain_url = domain_url + "?auction_type=live%20offer"
                elif property_detail.sale_by_type_id == 2:
                    notif_type = 8
                    domain_url = domain_url + "?auction_type=insider%20auction"

                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                asset_type = property_detail.property_asset.name
                template_data = {"domain_id": site_id, "slug": "listing_approval"}
                extra_data = {
                    'property_user_name': property_user_name,
                    'property_approved_status': property_approved_status,
                    'web_url': web_url,
                    'property_image': image_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'auction_type': auction_type,
                    'asset_type': asset_type,
                    'starting_price': "$" + number_format(start_price) if not auction_data.un_priced else 'Unpriced',
                    'starting_bid_offer': 'Starting Bid' if property_detail.sale_by_type_id in [1, 6] else "Asking Price",
                    'dashboard_link': domain_url,
                    "domain_id": site_id
                }
                compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
            except Exception as exp:
                pass
            # send notif to agent for approved or not approved
            try:
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id
                # check who approved/not approved
                if is_approved and int(is_approved) == 1:
                    content = "Your listing has been approved! <span>[" + prop_name + "]</span>"
                    owner_content = "You approved a listing! <span>[" + prop_name + "]</span>"
                else:
                    content = "Your listing has been made Unapproved! <span>[" + prop_name + "]</span>"
                    owner_content = "You Unapproved a listing! <span>[" + prop_name + "]</span>"
                if property_detail.agent_id != user_id:
                    # send notif to agent person for approved/not approved
                    add_notification(
                        site_id,
                        "Listing Approval",
                        content,
                        user_id=property_detail.agent_id,
                        added_by=property_detail.agent_id,
                        notification_for=2,
                        property_id=property_id,
                        notification_type=notif_type
                    )
                #  add notif to owner for for approval/not approval
                add_notification(
                    site_id,
                    "Listing Approval",
                    owner_content,
                    user_id=user_id,
                    added_by=user_id,
                    notification_for=2,
                    property_id=property_id,
                    notification_type=notif_type
                )

            except Exception as e:
                pass
            return Response(response.parsejson("Approval changed successfully..", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AllPropertyDeleteApiView(APIView):
    """
    Property approval change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            # data = request.data
            # delete_table = [
            #     PropertySubtype, PropertyTermAccepted, PropertyOccupiedBy, PropertyOwnership, PropertyPossession, PropertyStyle, PropertyCooling, PropertyStories, PropertyHeating,
            #     PropertyElectric, PropertyGas, PropertyRecentUpdates, PropertyWater, PropertySecurityFeatures, PropertySewer, PropertyTaxExemptions, PropertyZoning, PropertyAmenities,
            #     PropertyKitchenFeatures, PropertyAppliances, PropertyFlooring, PropertyWindows, PropertyBedroomFeatures, PropertyOtherRooms, PropertyBathroomFeatures, PropertyOtherFeatures,
            #     PropertyMasterBedroomFeatures, PropertyFireplaceType, PropertyBasementFeatures, PropertyHandicapAmenities, PropertyConstruction, PropertyGarageParking, PropertyExteriorFeatures,
            #     PropertyGarageFeatures, PropertyRoof, PropertyOutbuildings, PropertyFoundation, PropertyLocationFeatures, PropertyFence, PropertyRoadFrontage, PropertyPool,
            #     PropertyPropertyFaces, PropertyLeaseType, PropertyTenantPays, PropertyInclusions, PropertyBuildingClass, PropertyInteriorFeatures, PropertyMineralRights, PropertyEasements,
            #     PropertySurvey, PropertyUtilities, PropertyImprovements, PropertyTopography, PropertyWildlife, PropertyFish, PropertyIrrigationSystem, PropertyRecreation, PropertyAuction, PropertyUploads,
            #     PropertyListing
            # ]
            # for table in delete_table:
            #     table.objects.all().delete()
            return Response(response.parsejson("Delete table successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPropertyStatusChangeApiView(APIView):
    """
    Admin property status change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("You are not authentic user to update property.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = data['status']
            else:
                # Translators: This message appears when status is empty
                return Response(response.parsejson("status is required", "", status=403))

            PropertyListing.objects.filter(id=property_id).update(status_id=status)
            return Response(response.parsejson("Status changed successfully..", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPropertyApprovalChangeApiView(APIView):
    """
    Admin property approval change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("You are not authentic user to update property.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            if "is_approved" in data and data['is_approved'] != "":
                is_approved = data['is_approved']
            else:
                # Translators: This message appears when is_approved is empty
                return Response(response.parsejson("is_approved is required", "", status=403))
            
            try:
                property_detail = PropertyListing.objects.get(id=property_id)
                broker_data = Users.objects.get(site_id=property_detail.domain_id)
                prop_name = property_detail.address_one if property_detail.address_one else property_detail.id
                if is_approved and int(is_approved) == 1:
                    property_approved_status = "approved"
                    content = "Your listing has been approved! <span>[" + prop_name + "]</span>"
                    owner_content = "Admin approved a listing! <span>[" + prop_name + "]</span>"
                else:
                    property_approved_status = 'unapproved'
                    content = "Your listing has been made Unapproved! <span>[" + prop_name + "]</span>"
                    owner_content = "Admin Unapproved a listing! <span>[" + prop_name + "]</span>"
                # send email to agent for approval/not approval
                agent_data = property_detail.agent
                property_user_name = agent_data.first_name
                agent_email = agent_data.email
                auction_type = property_detail.sale_by_type.auction_type
                auction_data = PropertyAuction.objects.get(property=property_id)
                start_price = auction_data.start_price
                upload = None
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = 'https://realtyonegroup.s3.us-west-1.amazonaws.com/'+bucket_name+'/'+image
                subdomain_url = settings.SUBDOMAIN_URL
                network = NetworkDomain.objects.filter(id=property_detail.domain_id, is_active=1).first()
                domain_name = network.domain_name

                domain_url = subdomain_url.replace("###", domain_name)+"admin/listing/"
                notif_type =  2
                if property_detail.sale_by_type_id == 7:
                    notif_type = 6
                    domain_url = domain_url + "?auction_type=highest%20offer"
                elif property_detail.sale_by_type_id == 4:
                    notif_type = 4
                    domain_url = domain_url + "?auction_type=traditional%20offer"
                elif property_detail.sale_by_type_id == 6:
                    notif_type = 7
                    domain_url = domain_url + "?auction_type=live%20offer"

                property_address = property_detail.address_one
                property_city = property_detail.city
                property_state = property_detail.state.state_name
                asset_type = property_detail.property_asset.name
                template_data = {"domain_id": property_detail.domain_id, "slug": "listing_approval"}
                extra_data = {
                    'property_user_name': property_user_name,
                    'property_approved_status': property_approved_status,
                    'web_url': web_url,
                    'property_image': image_url,
                    'property_address': property_address,
                    'property_city': property_city,
                    'property_state': property_state,
                    'auction_type': auction_type,
                    'asset_type': asset_type,
                    'starting_price': "$" + number_format(start_price) if not auction_data.un_priced else 'Unpriced',
                    'starting_bid_offer': 'Starting Bid' if property_detail.sale_by_type_id in [1, 6] else "Asking Price",
                    'dashboard_link': domain_url,
                    "domain_id": property_detail.domain_id
                }
                compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)
                # check if owner and aget not same then send email to broker
                if property_detail.agent_id != broker_data.id:
                    property_user_name = broker_data.first_name 
                    broker_email = broker_data.email
                    extra_data = {'property_user_name': property_user_name, 'property_approved_status': property_approved_status, 'web_url': web_url, 'property_image': image_url, 'property_address': property_address, 'property_city': property_city, 'property_state': property_state, 'auction_type': auction_type, 'asset_type': asset_type, 'starting_price': start_price, 'dashboard_link': domain_url, "domain_id": property_detail.domain_id}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
                
                #  add notif to owner for for approval/not approval
                add_notification(
                    property_detail.domain_id,
                    "Listing Approval",
                    owner_content,
                    user_id=broker_data.id,
                    added_by=user_id,
                    notification_for=2,
                    property_id=property_id,
                    notification_type=notif_type
                )
                # check if owner and agent not same
                if property_detail.agent_id != broker_data.id:
                    # send notif to agent person for approved/not approved
                    add_notification(
                        property_detail.domain_id,
                        "Listing Approval",
                        content,
                        user_id=property_detail.agent_id,
                        added_by=user_id,
                        notification_for=2,
                        property_id=property_id,
                        notification_type=notif_type
                    )
            except Exception as e:
                pass

            PropertyListing.objects.filter(id=property_id).update(is_approved=is_approved)
            return Response(response.parsejson("Approval changed successfully..", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyViewApiView(APIView):
    """
    Add property view
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            property_data = PropertyListing.objects.get(id=property_id)
            if property_data is None:
                return Response(response.parsejson("Property not exist.", "", status=403))
            # elif property_data.agent_id == user_id:
            #     return Response(response.parsejson("You are owner", "", status=403))
            view_data = PropertyView.objects.filter(domain=site_id, property=property_id, user=user_id).first()
            if view_data is None:
                view_data = PropertyView()
                view_data.domain_id = site_id
                view_data.property_id = property_id
                view_data.user_id = user_id
                view_data.save()
            return Response(response.parsejson("Save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainPropertySuggestionApiView(APIView):
    """
    Subdomain property suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            property_listing = PropertyListing.objects.annotate(data=F('address_one')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('city')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('state__state_name')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('property_asset__name')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('sale_by_type__auction_type')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=Concat('agent__user_business_profile__first_name', V(' '), 'agent__user_business_profile__last_name')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('postal_code')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '), 'postal_code', output_field=CharField())).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FrontPropertySuggestionApiView(APIView):
    """
    Front property suggestion
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            property_listing = PropertyListing.objects.annotate(data=F('address_one')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('city')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('state__state_name')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('property_asset__name')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('sale_by_type__auction_type')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('postal_code')).filter(domain=site_id, data__icontains=search).exclude(status=5).values("data")
            searched_data = searched_data + list(property_listing)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeletePropertyApiView(APIView):
    """
    Delete property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("You are not authorised to delete property.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            PropertyListing.objects.filter(id=property_id, domain=site_id).update(status=5)
            return Response(response.parsejson("Property deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SavePropertySettingApiView(APIView):
    """
    Save property setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("You are not authorised to update setting.", "", status=403))
                data['user'] = user_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                data['property'] = int(data['property_id'])
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))

            if "time_flash" in data and data['time_flash'] != "":
                time_flash = int(data['time_flash'])
            else:
                return Response(response.parsejson("time_flash is required", "", status=403))

            if "auto_approval" in data and int(data['auto_approval']) == 1:
                if "bid_limit" in data and data['bid_limit'] != "":
                    bid_limit = int(data['bid_limit'])
                    data['bid_limit'] = bid_limit
                else:
                    return Response(response.parsejson("bid_limit is required", "", status=403))
            else:
                data['bid_limit'] = None

            if "is_deposit_required" in data and data['is_deposit_required'] != "":
                is_deposit_required = int(data['is_deposit_required'])
            else:
                return Response(response.parsejson("is_deposit_required is required", "", status=403))

            if "deposit_amount" in data and data['deposit_amount'] != "":
                deposit_amount = data['deposit_amount']
            elif is_deposit_required == 1:
                return Response(response.parsejson("deposit_amount is required", "", status=403))    

            property_settings = PropertySettings.objects.filter(domain=site_id, property=int(data['property_id']), status=1, is_agent=0, is_broker=0).first()
            data['status'] = 1
            serializer = SavePropertySettingSerializer(property_settings, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            property_auction_data = PropertyAuction.objects.filter(property=property_id).last()
            all_data = {"property_id": property_id, "auction_id": property_auction_data.id, "auction_type": property_auction_data.auction_id}
            return Response(response.parsejson("Setting save successfully.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SaveGlobalPropertySettingApiView(APIView):
    """
    Save global property setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
                data['domain'] = site_id
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                setting_type = "broker"
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    setting_type = "agent"
                    if users is None:
                        return Response(response.parsejson("You are not authorised to update setting.", "", status=403))
                data['user'] = user_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "time_flash" in data and data['time_flash'] != "":
                time_flash = int(data['time_flash'])
            else:
                return Response(response.parsejson("time_flash is required", "", status=403))

            if "auto_approval" in data and int(data['auto_approval']) == 1:
                if "bid_limit" in data and data['bid_limit'] != "":
                    bid_limit = int(data['bid_limit'])
                    data['bid_limit'] = bid_limit
                else:
                    return Response(response.parsejson("bid_limit is required", "", status=403))
            else:
                data['bid_limit'] = None

            if "is_deposit_required" in data and data['is_deposit_required'] != "":
                is_deposit_required = int(data['is_deposit_required'])
            else:
                return Response(response.parsejson("is_deposit_required is required", "", status=403))

            if "deposit_amount" in data and data['deposit_amount'] != "":
                deposit_amount = data['deposit_amount']
            elif is_deposit_required == 1:
                return Response(response.parsejson("deposit_amount is required", "", status=403))    

            data['status'] = 1
            data['property'] = None
            if setting_type == "broker":
                data['is_broker'] = 1
                data['is_agent'] = 0
                property_settings = PropertySettings.objects.filter(domain=site_id, is_agent=0, is_broker=1, status=1).first()
            else:
                data['is_broker'] = 0
                data['is_agent'] = 1
                property_settings = PropertySettings.objects.filter(domain=site_id, is_agent=1, is_broker=0, status=1).first()
            serializer = SavePropertySettingSerializer(property_settings, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Setting save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class GetPropertySettingApiView(APIView):
    """
    Get property setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            property_id = None
            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])

            is_broker = 0
            if "is_broker" in data and data['is_broker'] != "":
                is_broker = int(data['is_broker'])

            is_agent = 0
            if "is_agent" in data and data['is_agent'] != "":
                is_agent = int(data['is_agent'])

            property_settings = PropertySettings.objects.get(domain=site_id, property=property_id, is_broker=is_broker, is_agent=is_agent, status=1)
            serializer = PropertySettingSerializer(property_settings)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MakeFavouritePropertyApiView(APIView):
    """
    Make favourite property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type__in=[1, 2]).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__domain=site_id, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            favourite_property = FavouriteProperty.objects.filter(domain=site_id, property=property_id, user=user_id).first()
            if favourite_property is None:
                serializer = FavouritePropertySerializer(data=data)
                if serializer.is_valid():
                    data = serializer.save()
                    prop_name = data.property.address_one if data.property.address_one else data.property.id
                    content = "Listing added to favorites! <span>[" + prop_name + "]</span>"
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            else:
                prop_name = favourite_property.property.address_one if favourite_property.property.address_one else favourite_property.property.id
                favourite_property.delete()
                content = "Listing removed from favorites! <span>[" + prop_name + "]</span>"
            
            add_notification(
                site_id,
                "Listing Favorite",
                content,
                user_id=user_id,
                added_by=user_id,
                notification_for=1,
                property_id=property_id
            )
            return Response(response.parsejson("Save data successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FavouritePropertyListingApiView(APIView):
    """
    Favourite property listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = int(data['user'])
                users = Users.objects.filter(id=user, site=domain, status=1, user_type__in=[1, 2]).first()
                if users is None:
                    users = Users.objects.filter(id=user, status=1, network_user__domain=domain, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            favourite_property = FavouriteProperty.objects.filter(domain=domain, user=user)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    favourite_property = favourite_property.filter(Q(id=search))
                else:
                    favourite_property = favourite_property.annotate(property_name=Concat('property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(Q(property__address_one__icontains=search) | Q(property__city__icontains=search) | Q(property__state__state_name__icontains=search) | Q(property__sale_by_type__auction_type__icontains=search) | Q(property__property_asset__name__icontains=search) | Q(property_name__icontains=search))

            total = favourite_property.count()
            favourite_property = favourite_property.order_by("-id").only("id")[offset: limit]
            serializer = FavouritePropertyListingSerializer(favourite_property, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeleteFavouritePropertyApiView(APIView):
    """
    Delete favourite property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = int(data['user'])
                users = Users.objects.filter(id=user, site=domain, status=1, user_type__in=[1, 2]).first()
                if users is None:
                    users = Users.objects.filter(id=user, status=1, network_user__domain=domain, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))
            
            try:
                property_details = PropertyListing.objects.get(id=property_id)
                prop_name = property_details.address_one if property_details.address_one else property_details.id
                content = "Listing removed from favorites! <span>[" + prop_name + "]</span>"
                add_notification(
                    domain,
                    "Listing Favorite",
                    content,
                    user_id=user,
                    added_by=user,
                    notification_for=1,
                    property_id=property_id
                )
            except:
                pass

            FavouriteProperty.objects.filter(domain=domain, user=user, property=property_id).delete()
            return Response(response.parsejson("Data deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class FavouriteSuggestionApiView(APIView):
    """
    Front property suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            property_listing = FavouriteProperty.objects.annotate(data=F('property__address_one')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = FavouriteProperty.objects.annotate(data=F('property__city')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = FavouriteProperty.objects.annotate(data=F('property__state__state_name')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = FavouriteProperty.objects.annotate(data=F('property__sale_by_type__auction_type')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = FavouriteProperty.objects.annotate(data=F('property__postal_code')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            property_listing = FavouriteProperty.objects.annotate(data=F('property__property_asset__name')).filter(domain=site_id, user=user_id, data__icontains=search).values("data")
            searched_data = searched_data + list(property_listing)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class MakeWatchPropertyApiView(APIView):
    """
    Make watch property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type__in=[1, 2]).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__domain=site_id,
                                                 user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            watch_property = WatchProperty.objects.filter(domain=site_id, property=property_id, user=user_id).first()
            if watch_property is None:
                serializer = WatchPropertySerializer(data=data)
                if serializer.is_valid():
                    serializer.save()
                else:
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
            else:
                watch_property.delete()
            return Response(response.parsejson("Save data successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ScheduleTourApiView(APIView):
    """
    Schedule tour
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=site_id).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "schedule_date" in data and data['schedule_date'] != "":
                schedule_date = data['schedule_date']
            else:
                return Response(response.parsejson("schedule_date is required", "", status=403))

            if "tour_type" not in data or data['tour_type'] == "":
                return Response(response.parsejson("tour_type is required", "", status=403))
            elif int(data['tour_type']) == 1:
                tour_type = 'In-Person'
            else:
                tour_type = 'Video Chat'
                    
            if "first_name" not in data or data['first_name'] == "":
                return Response(response.parsejson("first_name is required", "", status=403))

            if "last_name" not in data or data['last_name'] == "":
                return Response(response.parsejson("last_name is required", "", status=403))

            if "email" in data and data['email'] != "":
                email = data['email']
                try:
                    validate_email(email)
                except ValidationError:
                    # Translators: This message appears when email is invalid
                    return Response(response.parsejson("Invalid email address", "", status=404))
            else:
                return Response(response.parsejson("email is required", "", status=403))

            if "phone_no" not in data or data['phone_no'] == "":
                return Response(response.parsejson("phone_no is required", "", status=403))

            if "availability" not in data or data['availability'] == "":
                return Response(response.parsejson("availability is required", "", status=403))
            elif int(data['availability']) == 1:
                availability = 'Morning'
            elif int(data['availability']) == 2:
                availability = 'Afternoon'
            elif int(data['availability']) == 3:
                availability = 'Evening'
            else:
                availability = 'Flexible'        

            data['status'] = 1
            serializer = ScheduleTourSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            
            try:
                #----Send Email---------------------
                subdomain_url = settings.SUBDOMAIN_URL
                domain_name = network.domain_name
                domain_admin_url = subdomain_url.replace("###", domain_name)+"admin/schedule-tour-list/"
                property_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(property_id)
                property_button = 'property-btn.jpg' 
                dashboard_button = 'dashboard-btn.jpg'
                # if int(users.user_type.id) == 2 and users.site_id is None:
                #     dashboard_text = 'dashboard-btn.jpg'
                #     domain_url = subdomain_url.replace("###", domain_name)+"admin/schedule-tour-list/"
                # else:
                #     dashboard_text = 'property-btn.jpg' 
                #     domain_url = subdomain_url.replace("###", domain_name)+"asset-details/?property_id="+str(property_id)
                number = data['phone_no']
                buyer_email = users.email
                property_detail = PropertyListing.objects.get(id=property_id)
                agent_datail = property_detail.agent
                agent_name = agent_datail.first_name
                agent_email = agent_datail.email
                broker_detail = Users.objects.get(site_id=site_id)
                broker_name = broker_detail.first_name
                broker_email = broker_detail.email
                chat_message = data['message'] if data['message'] !="" else None
                template_data = {"domain_id": site_id, "slug": "virtual_tour"}
                upload = PropertyUploads.objects.filter(property=property_id, upload_type=1).first()
                web_url = settings.FRONT_BASE_URL
                image_url = web_url+'/static/admin/images/property-default-img.png'
                date = data['schedule_date'].split( )
                if upload is not None:
                    image = upload.upload.doc_file_name
                    bucket_name = upload.upload.bucket_name
                    image_url = settings.AWS_URL+bucket_name+'/'+image
                
                content_text = "Thank you for Requesting for property tour.<br/>Admin has received your request and is currently under review"
                if buyer_email.lower() == agent_email.lower():
                    extra_data = {"user_name": data['first_name'], 'web_url': settings.FRONT_BASE_URL, 'property_image': image_url, 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': chat_message, 'tour_person_name': data['first_name'], 'tour_type': tour_type, 'tour_date': date[0], 'tour_availability': availability, 'tour_person_phone': phone_format(number), 'tour_person_email': data['email'], 'tour_comment': chat_message, 'dashboard_link': property_url, "domain_id": site_id, "content_text": content_text, 'dashboard_text': property_button}
                    compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)
                else:
                    extra_data = {"user_name": data['first_name'], 'web_url': settings.FRONT_BASE_URL, 'property_image': image_url, 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': chat_message, 'tour_person_name': data['first_name'], 'tour_type': tour_type, 'tour_date': date[0], 'tour_availability': availability, 'tour_person_phone': phone_format(number), 'tour_person_email': data['email'], 'tour_comment': chat_message, 'dashboard_link': property_url, "domain_id": site_id, "content_text": content_text, 'dashboard_text': property_button}
                    compose_email(to_email=[email], template_data=template_data, extra_data=extra_data)

                    content_text = 'You have Received One Request for Schedule Tour By Buyer'
                    extra_data = {"user_name": agent_name, 'web_url': settings.FRONT_BASE_URL, 'property_image': image_url, 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': chat_message, 'tour_person_name': data['first_name'], 'tour_type': tour_type, 'tour_date': date[0], 'tour_availability': availability, 'tour_person_phone': phone_format(number), 'tour_person_email': data['email'], 'tour_comment': chat_message, 'dashboard_link': domain_admin_url, "domain_id": site_id, "content_text": content_text, 'dashboard_text': dashboard_button}
                    compose_email(to_email=[agent_email], template_data=template_data, extra_data=extra_data)

                if buyer_email.lower() != broker_email.lower() and agent_email.lower() != broker_email.lower():
                    content_text = 'You have Received One Request for Schedule Tour By Buyer'
                    extra_data = {"user_name": broker_name, 'web_url': settings.FRONT_BASE_URL, 'property_image': image_url, 'property_name': data['property_name'], 'property_address': data['property_address'], 'property_city':data['property_city'], 'property_state': data['property_state'], 'property_zipcode': data['property_zipcode'], 'chat_message': chat_message, 'tour_person_name': data['first_name'], 'tour_type': tour_type, 'tour_date': date[0], 'tour_availability': availability, 'tour_person_phone': phone_format(number), 'tour_person_email': data['email'], 'tour_comment': chat_message, 'dashboard_link': domain_admin_url, "domain_id": site_id, "content_text": content_text, 'dashboard_text': dashboard_button}
                    compose_email(to_email=[broker_email], template_data=template_data, extra_data=extra_data)
            except:
                pass

            return Response(response.parsejson("Save data successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ScheduleTourDetailApiView(APIView):
    """
    Schedule tour detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=site_id).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))
            serializer = ScheduleTourDetailSerializer(users)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminScheduleTourListingApiView(APIView):
    """
    Super admin schedule tour listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            domain = None
            if "domain" in data and type(data['domain']) == list and len(data['domain']) > 0:
                domain = data['domain']

            schedule_tour = ScheduleTour.objects
            if domain is not None and len(domain) > 0:
                schedule_tour = schedule_tour.filter(domain__in=domain)
            
            if "status" in data and type(data["status"]) == list and len(data["status"]) > 0:
                schedule_tour = schedule_tour.filter(status__in=data["status"])
            
            if "tour_type" in data and type(data["tour_type"]) == list and len(data["tour_type"]) > 0:
                schedule_tour = schedule_tour.filter(tour_type__in=data["tour_type"])
            
            if "availability" in data and type(data["availability"]) == list and len(data["availability"]) > 0:
                schedule_tour = schedule_tour.filter(availability__in=data["availability"])

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    schedule_tour = schedule_tour.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(Q(phone_no__icontains=search) | Q(property_name__icontains=search))
                else:
                    tour_type = {"in person": 1, "virtual tour": 2}
                    availability = {"morning": 1, "afternoon": 2, "evening": 3, "flexible": 4}
                    tour_search = availability_search = 111
                    if search.lower() in tour_type:
                        tour_search = tour_type[search.lower()]
                    if search.lower() in availability:
                        availability_search = availability[search.lower()]
                        
                    schedule_tour = schedule_tour\
                        .annotate(property_name=Concat(
                            'property__address_one', V(', '),
                            'property__city', V(', '),
                            'property__state__state_name', V(' '),
                            'property__postal_code', output_field=CharField()))\
                        .annotate(full_name=Concat('first_name', V(' '), 'last_name'))\
                        .filter(
                            Q(domain__domain_name__icontains=search) |
                            Q(first_name__icontains=search) |
                            Q(last_name__icontains=search) |
                            Q(message__icontains=search) |
                            Q(status__status_name__icontains=search) |
                            Q(property_name__icontains=search) |
                            Q(full_name__icontains=search) |
                            Q(email__icontains=search) |
                            Q(user__status__status_name__icontains=search) |
                            Q(tour_type=tour_search) |
                            Q(availability=availability_search)
                        )

            total = schedule_tour.count()
            schedule_tour = schedule_tour.order_by("-id").only("id")[offset: limit]
            serializer = SuperAdminScheduleTourSerializer(schedule_tour, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainScheduleTourListingApiView(APIView):
    """
    Subdomain schedule tour listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = data['user_id']
                user = Users.objects.filter(id=user_id, status=1, site=domain).first()
                if user is None:
                    network_user = NetworkUser.objects.filter(domain=domain, user=user_id, status=1, user__status=1, is_agent=1).first()
                    if network_user is None:
                        return Response(response.parsejson("You are not authorised to update.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required", "", status=403))

            schedule_tour = ScheduleTour.objects.filter(Q(domain=domain) & (Q(property__agent=user_id) | Q(property__domain__users_site_id__id=user_id)))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    schedule_tour = schedule_tour.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(Q(user__phone_no__icontains=search) | Q(property_name__icontains=search))
                else:
                    tour_type = {"in person": 1, "virtual tour": 2}
                    tour_search = 111
                    if search.lower() in tour_type:
                        tour_search = tour_type[search.lower()]

                    availability = {"morning": 1, "afternoon": 2, "evening": 3, "flexible": 4}
                    availability_search = 111
                    if search.lower() in availability:
                        availability_search = availability[search.lower()]

                    schedule_tour = schedule_tour.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(Q(domain__domain_name__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(message__icontains=search) | Q(status__status_name__icontains=search) | Q(property_name__icontains=search) | Q(full_name__icontains=search) | Q(email__icontains=search) | Q(user__status__status_name__icontains=search) | Q(tour_type=tour_search) | Q(availability=availability_search))

            total = schedule_tour.count()
            schedule_tour = schedule_tour.order_by("-id").only("id")[offset: limit]
            serializer = SubdomainScheduleTourSerializer(schedule_tour, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DocumentVaultVisitApiView(APIView):
    """
    Document vault visit
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=site_id).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "documents" in data and data['documents'] != "":
                documents = int(data['documents'])
                property_uploads = PropertyUploads.objects.filter(id=documents, property=property_id, upload_type=3, property__domain=site_id, status=1).first()
                if property_uploads is None:
                    return Response(response.parsejson("Please enter valid documents.", "", status=403))
            else:
                return Response(response.parsejson("documents is required", "", status=403))

            data['status'] = 1
            document_vault_visit = DocumentVaultVisit.objects.filter(domain=site_id, property=property_id, user=user_id, documents=documents, status=1).first()
            serializer = DocumentVaultVisitSerializer(document_vault_visit, data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                copy_errors = serializer.errors.copy()
                return Response(response.parsejson(copy_errors, "", status=403))
            return Response(response.parsejson("Added successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyUploadDetailApiView(APIView):
    """
    Property upload detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, network_user__domain=site_id).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "property" in data and data['property'] != "":
                property_id = int(data['property'])
            else:
                return Response(response.parsejson("property is required", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
                property_uploads = PropertyUploads.objects.filter(upload=upload_id, property=property_id, upload_type=3, property__domain=site_id, status=1).first()
                if property_uploads is None:
                    return Response(response.parsejson("Please enter valid upload id.", "", status=403))
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))
            all_data = {
                "upload_id": upload_id,
                "doc_file_name": property_uploads.upload.doc_file_name,
                "bucket_name": property_uploads.upload.bucket_name,
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyListingOrderingApiView(APIView):
    """
    Property listing ordering
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                site_id = int(data['domain'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, user_type=2, network_user__domain=site_id).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "ordering" in data and type(data['ordering']) == dict and len(data['ordering']) > 0:
                ordering = data['ordering']
            else:
                return Response(response.parsejson("ordering is required", "", status=403))
            for key, value in ordering.items():
                try:
                    PropertyListing.objects.filter(Q(id=int(key)) & Q(domain=site_id) & (Q(agent=user_id) | Q(domain__users_site_id__id=user_id))).update(ordering=value)
                except Exception as exp:
                    pass
            return Response(response.parsejson("Successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainScheduleTourSuggestionApiView(APIView):
    """
    Subdomain schedule tour suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user" in data and data['user'] != "":
                user_id = int(data['user'])
                users = Users.objects.filter(id=user_id, site=site_id, status=1, user_type=2).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, status=1, network_user__status=1, user_type=2, network_user__domain=site_id, network_user__is_agent=1).first()
                    if users is None:
                        return Response(response.parsejson("Not site user.", "", status=201))
            else:
                return Response(response.parsejson("user is required", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            schedule_tour = ScheduleTour.objects.annotate(data=F('domain__domain_name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(schedule_tour)

            schedule_tour = ScheduleTour.objects.annotate(data=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(schedule_tour)

            schedule_tour = ScheduleTour.objects.annotate(data=Concat('first_name', V(' '), 'last_name')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(schedule_tour)

            schedule_tour = ScheduleTour.objects.annotate(data=F('phone_no')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(schedule_tour)

            schedule_tour = ScheduleTour.objects.annotate(data=F('email')).filter(domain=site_id, data__icontains=search).values("data")
            searched_data = searched_data + list(schedule_tour)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminFavouritePropertyListingApiView(APIView):
    """
    Super admin favourite property listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            favourite_property = FavouriteProperty.objects
            if "listing_id" in data and data['listing_id']:
                favourite_property = favourite_property.filter(property__id=data['listing_id'])

            if "domain" in data and type(data['domain']) == list and len(data['domain']) > 0:
                favourite_property = favourite_property.filter(domain__in=data['domain'])
            
            if "asset_type" in data and type(data['asset_type']) == list and len(data['asset_type']) > 0:
                favourite_property= favourite_property.filter(property__property_asset__in=data['asset_type'])
            
            if "auction_type" in data and type(data['auction_type']) == list and len(data['auction_type']) > 0:
                favourite_property = favourite_property.filter(property__sale_by_type__in=data['auction_type'])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    favourite_property = favourite_property\
                        .annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField()))\
                        .filter(
                            Q(id=search) |
                            Q(property_name__icontains=search)
                        )
                else:
                    favourite_property = favourite_property\
                        .annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField()))\
                        .annotate(name=Concat('user__first_name', V(' '), 'user__last_name', output_field=CharField()))\
                        .filter(
                            Q(property__address_one__icontains=search) |
                            Q(property__city__icontains=search) |
                            Q(property__state__state_name__icontains=search) |
                            Q(property__sale_by_type__auction_type__icontains=search) |
                            Q(property__property_asset__name__icontains=search) |
                            Q(property_name__icontains=search) |
                            Q(name__icontains=search) | 
                            Q(user__first_name__icontains=search) |
                            Q(user__last_name__icontains=search) |
                            Q(user__email__icontains=search) |
                            Q(domain__domain_name__icontains=search)
                        )

            total = favourite_property.count()
            favourite_property = favourite_property.order_by("id").only("id")[offset: limit]
            serializer = SuperAdminFavouritePropertyListingSerializer(favourite_property, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminDeleteFavouritePropertyApiView(APIView):
    """
    Super admin delete favourite property
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1, user_type__in=[3]).first()
                if users is None:
                    return Response(response.parsejson("Not authorised for this action.", "", status=201))
            else:
                return Response(response.parsejson("admin_id is required", "", status=403))

            if "favourite_id" in data and data['favourite_id'] != "":
                favourite_id = int(data['favourite_id'])
            else:
                return Response(response.parsejson("favourite_id is required", "", status=403))

            fav_prop = FavouriteProperty.objects.filter(id=favourite_id).first()
            try:
                prop_name = fav_prop.property.address_one if fav_prop.property.address_one else fav_prop.property.id
                content = "Listing removed from favorites! <span>[" + prop_name + "]</span>"
                add_notification(
                    fav_prop.domain_id,
                    "Listing Favorite",
                    content,
                    user_id=fav_prop.user_id,
                    added_by=admin_id,
                    notification_for=1,
                    property_id=fav_prop.property_id
                )
            except:
                pass
            
            fav_prop.delete()

            return Response(response.parsejson("Data deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertySettingApiView(APIView):
    """
    Property setting
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required", "", status=403))
            all_data = {}
            property_settings = PropertySettings.objects.filter(domain=domain_id, property=property_id, is_broker=0, is_agent=0, status=1).first()
            if property_settings is not None:
                all_data['is_log_time_extension'] = property_settings.is_log_time_extension
                all_data['time_flash'] = property_settings.time_flash
                all_data['remain_time_to_add_extension'] = property_settings.remain_time_to_add_extension
                all_data['log_time_extension'] = property_settings.log_time_extension
            else:
                property_settings = PropertySettings.objects.filter(domain=domain_id, is_broker=0, is_agent=1, status=1).first()
                if property_settings is not None:
                    all_data['is_log_time_extension'] = property_settings.is_log_time_extension
                    all_data['time_flash'] = property_settings.time_flash
                    all_data['remain_time_to_add_extension'] = property_settings.remain_time_to_add_extension
                    all_data['log_time_extension'] = property_settings.log_time_extension
                else:
                    property_settings = PropertySettings.objects.filter(domain=domain_id, is_broker=1, is_agent=0, status=1).first()
                    if property_settings is not None:
                        all_data['is_log_time_extension'] = property_settings.is_log_time_extension
                        all_data['time_flash'] = property_settings.time_flash
                        all_data['remain_time_to_add_extension'] = property_settings.remain_time_to_add_extension
                        all_data['log_time_extension'] = property_settings.log_time_extension
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyAuctionDashboardApiView(APIView):
    """
    Property auction dashboard
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_agent = None
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        is_agent = True
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            property_data = PropertyListing.objects.filter(sale_by_type=1, is_approved=1)
            if domain_id is not None:
                property_data = property_data.filter(domain=domain_id)
            if is_agent is not None:
                property_data = property_data.filter(agent=user_id)

            if "status" in data and data['status'] != "":
                status = int(data['status'])
                if status == 1:
                    property_data = property_data.filter(Q(status=1) & Q(property_auction__start_date__lte=timezone.now()))
                    # property_data = property_data.filter(Q(status=1))
                elif status == 17:
                    property_data = property_data.filter(Q(status=1) & Q(property_auction__start_date__gt=timezone.now()))
                else:
                    property_data = property_data.filter(Q(status=status))

            # -----------------Filter-------------------
            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_data = property_data.filter(Q(agent=agent_id))

            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_data = property_data.filter(Q(sale_by_type=auction_id))

            if "asset_id" in data and data["asset_id"] != "":
                asset_id = int(data["asset_id"])
                property_data = property_data.filter(Q(property_asset=asset_id))

            # if "status" in data and data["status"] != "":
            #     status = int(data["status"])
            #     property_data = property_data.filter(Q(status=status))

            if "property_type" in data and data["property_type"] != "":
                property_type = int(data["property_type"])
                property_data = property_data.filter(Q(property_type=property_type))

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_data = property_data.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_data = property_data.annotate(
                    property_name=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '),
                                         'postal_code', output_field=CharField())).annotate(
                    full_name=Concat('agent__user_business_profile__first_name', V(' '),
                                     'agent__user_business_profile__last_name')).filter(
                    Q(property_asset__name__icontains=search) | Q(sale_by_type__auction_type__icontains=search) | Q(
                        agent__user_business_profile__company_name__icontains=search) | Q(
                        full_name__icontains=search) | Q(city__icontains=search) | Q(
                        address_one__icontains=search) | Q(state__state_name__icontains=search) | Q(
                        property_type__property_type__icontains=search) | Q(property_name__icontains=search))

            total = property_data.count()
            property_data = property_data.order_by(F("ordering").asc(nulls_last=True)).only("id")[offset:limit]
            serializer = PropertyAuctionDashboardSerializer(property_data, many=True)
            all_data = {
                "data": serializer.data,
                "total": total
            }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyAuctionSuggestionApiView(APIView):
    """
    Property auction suggestion
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
            else:
                return Response(response.parsejson("site_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                is_agent = None
                if users is None:
                    is_agent = True
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1,
                                                 network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                data["agent"] = user_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "search" in data and data['search'] != "":
                search = data['search']
            else:
                return Response(response.parsejson("search is required", "", status=403))
            searched_data = []

            property_listing = PropertyListing.objects.annotate(data=F('address_one')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('city')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('state__state_name')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('property_asset__name')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('sale_by_type__auction_type')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=Concat('agent__user_business_profile__first_name', V(' '), 'agent__user_business_profile__last_name')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=F('postal_code')).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            property_listing = PropertyListing.objects.annotate(data=Concat('address_one', V(', '), 'city', V(', '), 'state__state_name', V(' '), 'postal_code', output_field=CharField())).filter(domain=site_id, data__icontains=search).values("data")
            if is_agent:
                property_listing = property_listing.filter(agent=user_id)
            searched_data = searched_data + list(property_listing)

            searched_data = [i['data'] for i in searched_data]
            searched_data = list(set(searched_data))
            return Response(response.parsejson("Fetch data.", searched_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class StartStopAuctionApiView(APIView):
    """
    Start stop auction
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_agent = None
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        is_agent = True
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            property_auction = PropertyAuction.objects.filter(property=property_id)
            if domain_id is not None:
                property_auction = property_auction.filter(domain=domain_id)
            if is_agent:
                property_auction = property_auction.filter(property__agent=user_id)

            property_auction = property_auction.first()
            if property_auction is not None and property_auction.status_id == 1:
                property_auction.status_id = 2
            elif property_auction is not None and property_auction.status_id == 2:
                property_auction.status_id = 1
            else:
                property_auction.status_id = property_auction.status_id

            property_auction.save()
            return Response(response.parsejson("Data successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateBidIncrementApiView(APIView):
    """
    Update bid increment
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_agent = None
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        is_agent = True
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            if "bid_increments" in data and data['bid_increments'] != "":
                bid_increments = int(data['bid_increments'])
            else:
                return Response(response.parsejson("bid_increments is required.", "", status=403))

            property_auction = PropertyAuction.objects.filter(property=property_id)
            if domain_id is not None:
                property_auction = property_auction.filter(domain=domain_id)
            if is_agent:
                property_auction = property_auction.filter(property__agent=user_id)

            property_auction = property_auction.first()
            if property_auction is not None:
                property_auction.bid_increments = bid_increments

            property_auction.save()
            return Response(response.parsejson("Data successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateReserveAmountApiView(APIView):
    """
    Update reserve amount
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_agent = None
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        is_agent = True
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            if "reserve_amount" in data and data['reserve_amount'] != "":
                reserve_amount = int(data['reserve_amount'])
            else:
                return Response(response.parsejson("reserve_amount is required.", "", status=403))

            property_auction = PropertyAuction.objects.filter(property=property_id)
            if domain_id is not None:
                property_auction = property_auction.filter(domain=domain_id)
            if is_agent:
                property_auction = property_auction.filter(property__agent=user_id)

            property_auction = property_auction.first()
            if property_auction is not None:
                property_auction.reserve_amount = reserve_amount

            property_auction.save()
            return Response(response.parsejson("Data successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class UpdateAuctionDateApiView(APIView):
    """
    Update auction date
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                is_agent = None
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        is_agent = True
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1,
                                                     network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            if "start_date" in data and data['start_date'] != "":
                start_date = data['start_date']
            else:
                return Response(response.parsejson("start_date is required.", "", status=403))

            if "end_date" in data and data['end_date'] != "":
                end_date = data['end_date']
            else:
                return Response(response.parsejson("end_date is required.", "", status=403))

            property_auction = PropertyAuction.objects.filter(property=property_id)
            if domain_id is not None:
                property_auction = property_auction.filter(domain=domain_id)

            if is_agent:
                property_auction = property_auction.filter(property__agent=user_id)

            property_auction = property_auction.first()
            if property_auction is not None:
                property_auction.start_date = start_date
                property_auction.end_date = end_date

            property_auction.save()
            return Response(response.parsejson("Data successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AuctionListingReadApiView(APIView):
    """
    Auction listing read
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            is_super_admin = None
            if "is_super_admin" in data and data['is_super_admin'] != "":
                is_super_admin = int(data['is_super_admin'])

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                if is_super_admin is None:
                    return Response(response.parsejson("domain_id is required", "", status=403))
                else:
                    domain_id = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                if is_super_admin is None:
                    users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                    if users is None:
                        users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                        if users is None:
                            return Response(response.parsejson("User not exist.", "", status=403))
                else:
                    users = Users.objects.filter(id=user_id, status=1, user_type=3).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                return Response(response.parsejson("property_id is required.", "", status=403))

            property_listing = PropertyListing.objects.filter(id=property_id)
            if domain_id is not None:
                property_listing = property_listing.filter(domain=domain_id)
            property_listing = property_listing.first()
            property_listing.read_by_auction_dashboard = 1
            property_listing.save()
            return Response(response.parsejson("Data successfully updated.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyEvaluatorCategoryApiView(APIView):
    """
    Add Property Evaluator Category
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            category_id = None
            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "name" in data and data['name'] != "":
                name = data['name']
            else:
                return Response(response.parsejson("name is required", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required", "", status=403))

            property_evaluator_category = PropertyEvaluatorCategory()
            if category_id is not None:
                property_evaluator_category = PropertyEvaluatorCategory.objects.get(id=category_id)

            property_evaluator_category.name = name
            property_evaluator_category.status_id = status
            property_evaluator_category.save()
            return Response(response.parsejson("Category save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorCategoryListApiView(APIView):
    """
    Property Evaluator Category List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            property_evaluator_category = PropertyEvaluatorCategory.objects
            if 'search' in data and data['search'] != "":
                property_evaluator_category = property_evaluator_category.filter(name__icontains=data['search'])

            if 'status' in data and type(data['status'] == list) and len(data['status']) > 0:
                property_evaluator_category = property_evaluator_category.filter(status__in=data['status'])

            total = property_evaluator_category.count()
            property_evaluator_category = property_evaluator_category.order_by("-id").values("id", "name", status_name=F("status__status_name"))[offset: limit]
            all_data = {'total': total, 'data': property_evaluator_category}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorCategoryDetailApiView(APIView):
    """
    Property Evaluator Category Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])
            else:
                return Response(response.parsejson("category_id is required.", "", status=403))

            property_evaluator_category = PropertyEvaluatorCategory.objects.filter(id=category_id).values("id", "name", "status")
            return Response(response.parsejson("Fetch data.", property_evaluator_category, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPropertyEvaluatorQuestionApiView(APIView):
    """
    Add Property Evaluator Question
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            question_id = None
            if "question_id" in data and data['question_id'] != "":
                question_id = int(data['question_id'])

            placeholder = None
            if "placeholder" in data and data['placeholder'] != "":
                placeholder = data['placeholder']

            if "category" in data and data['category'] != "":
                category = int(data['category'])
            else:
                return Response(response.parsejson("category_id is required.", "", status=403))

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "question" in data and data['question'] != "":
                question = data['question']
            else:
                return Response(response.parsejson("question is required.", "", status=403))

            if "option_type" in data and data['option_type'] != "":
                option_type = int(data['option_type'])
            else:
                return Response(response.parsejson("option_type is required.", "", status=403))

            if "property_type" in data and data['property_type'] != "":
                property_type = int(data['property_type'])
            else:
                return Response(response.parsejson("property_type is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            question_option = None
            if "question_option" in data and type(data['question_option']) == list and len(data['question_option']) > 0:
                question_option = data['question_option']

            with transaction.atomic():
                try:
                    property_evaluator_question = PropertyEvaluatorQuestion.objects.filter(id=question_id).first()
                    serializer = AddPropertyEvaluatorQuestionSerializer(property_evaluator_question, data=data)
                    if serializer.is_valid():
                        question_id = serializer.save()
                        question_id = question_id.id
                    else:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        copy_errors = serializer.errors.copy()
                        return Response(response.parsejson(copy_errors, "", status=403))

                    if question_option is not None:
                        PropertyEvaluatorQuestionOption.objects.filter(question=question_id).delete()
                        for option in question_option:
                            property_evaluator_question_option=PropertyEvaluatorQuestionOption()
                            property_evaluator_question_option.question_id = question_id
                            property_evaluator_question_option.option = option
                            property_evaluator_question_option.status_id = 1
                            property_evaluator_question_option.save()

                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Question save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorQuestionListApiView(APIView):
    """
    Property Evaluator Question List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            property_evaluator_question = PropertyEvaluatorQuestion.objects
            if 'search' in data and data['search'] != "":
                property_evaluator_question = property_evaluator_question.filter(Q(question__icontains=data['search']) | Q(category__name__icontains=data['search']))

            if 'status' in data and type(data['status'] == list) and len(data['status']) > 0:
                property_evaluator_question = property_evaluator_question.filter(status__in=data['status'])

            total = property_evaluator_question.count()
            property_evaluator_question = property_evaluator_question.order_by("-id").values("id", "question", "option_type", status_name=F("status__status_name"), category_name=F("category__name"))
            all_data = {'total': total, 'data': property_evaluator_question}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorQuestionDetailApiView(APIView):
    """
    Property Evaluator Question Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "question_id" in data and data['question_id'] != "":
                question_id = int(data['question_id'])
            else:
                return Response(response.parsejson("question_id is required.", "", status=403))

            property_evaluator_question = PropertyEvaluatorQuestion.objects.get(id=question_id)
            serializer = PropertyEvaluatorQuestionDetailSerializer(property_evaluator_question)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SavePropertyEvaluatorAnswerApiView(APIView):
    """
    Save Property Evaluator Answer
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required.", "", status=403))

            option_type = None
            if "question_id" in data and data['question_id'] != "":
                question_id = int(data['question_id'])
                option_type = PropertyEvaluatorQuestion.objects.filter(id=question_id).first()
                option_type = option_type.option_type
            else:
                return Response(response.parsejson("question_id is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            answer = None
            answer_data = None
            if option_type != 4:
                if "answer" in data and data['answer'] != "":
                    answer = data['answer']
            elif option_type == 4 and "answer" in data and type(data['answer']) == list and len(data['answer']) > 0:
                answer_data = data['answer']

            with transaction.atomic():
                try:
                    property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(domain=domain_id, user=user_id).first()
                    property_evaluator_domain
                    if property_evaluator_domain is None:
                        property_evaluator_domain = PropertyEvaluatorDomain()
                        property_evaluator_domain.domain_id = domain_id
                        property_evaluator_domain.user_id = user_id
                        property_evaluator_domain.status_id = 1
                        property_evaluator_domain.save()
                        property_evaluator_id = property_evaluator_domain.id
                    else:
                        property_evaluator_id = property_evaluator_domain.id

                    property_evaluator_user_answer = PropertyEvaluatorUserAnswer.objects.filter(property_evaluator=property_evaluator_id, question=question_id).first()
                    if property_evaluator_user_answer is None:
                        property_evaluator_user_answer = PropertyEvaluatorUserAnswer()
                    property_evaluator_user_answer.property_evaluator_id = property_evaluator_id
                    property_evaluator_user_answer.question_id = question_id
                    property_evaluator_user_answer.answer = answer
                    property_evaluator_user_answer.save()
                    answer_id = property_evaluator_user_answer.id
                    if answer_data is not None and len(answer_data) > 0:
                        PropertyEvaluatorDocAnswer.objects.filter(answer=answer_id).delete()
                        for doc_id in answer_data:
                            property_evaluator_doc_answer = PropertyEvaluatorDocAnswer()
                            property_evaluator_doc_answer.answer_id = answer_id
                            property_evaluator_doc_answer.document_id = doc_id
                            property_evaluator_doc_answer.user_id = user_id
                            property_evaluator_doc_answer.save()
                    else:
                        PropertyEvaluatorDocAnswer.objects.filter(answer=answer_id).delete()

                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))

            if "is_last_question" in data and data['is_last_question'] != "" and data['is_last_question']:
                user_business_profile = UserBusinessProfile.objects.filter(user__site=domain_id).first()
                super_admin = Users.objects.filter(id=1, user_type=3, status=1).first()
                extra_data = {
                    "user_name": users.first_name + ' ' + users.last_name,
                    "domain_name": user_business_profile.company_name
                }
                # ------Email to Super Admin------
                # template_data = {"domain_id": domain_id, "slug": "received_property_bot_request"}
                # compose_email(to_email=[super_admin.email], template_data=template_data, extra_data=extra_data)

                # ------Email to Broker------
                template_data = {"domain_id": domain_id, "slug": "received_property_bot_request"}
                compose_email(to_email=[user_business_profile.user.email], template_data=template_data, extra_data=extra_data)

                # ------Email to Customer------
                template_data = {"domain_id": domain_id, "slug": "send_property_bot_request"}
                compose_email(to_email=[users.email], template_data=template_data, extra_data=extra_data)

            return Response(response.parsejson("Answer save successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorQuestionApiView(APIView):
    """
    Property Evaluator Question
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required.", "", status=403))

            business_profile = UserBusinessProfile.objects.filter(user__site=domain_id).first()

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))
            setting = PropertyEvaluatorSetting.objects.filter(domain=domain_id, status=1).order_by("property_type").values("id", "property_type_id")
            property_address = PropertyEvaluatorQuestion.objects.filter(category=1, status=1).order_by("id")
            property_address = PropertyEvaluatorQuestionSerializer(property_address, many=True, context={"user_id": user_id, "domain_id": domain_id})
            property_details = PropertyEvaluatorQuestion.objects.filter(category=2, status=1).order_by("id")
            property_details = PropertyEvaluatorQuestionSerializer(property_details, many=True, context={"user_id": user_id, "domain_id": domain_id})
            photos_document = PropertyEvaluatorQuestion.objects.filter(category=3, status=1).order_by("id")
            photos_document = PropertyEvaluatorQuestionSerializer(photos_document, many=True, context={"user_id": user_id, "domain_id": domain_id})
            additionals_questions = PropertyEvaluatorQuestion.objects.filter(category=4, status=1).order_by("id")
            additionals_questions = PropertyEvaluatorQuestionSerializer(additionals_questions, many=True, context={"user_id": user_id, "domain_id": domain_id})
            property_user_answer = PropertyEvaluatorUserAnswer.objects.filter(question=3, property_evaluator__domain=domain_id).first()
            property_type = None
            if property_user_answer is not None:
                property_type = property_user_answer.answer
            all_data = {"property_address": property_address.data, "property_details": property_details.data, "photos_document": photos_document.data, "additionals_questions": additionals_questions.data, "property_type": property_type, "domain_name": business_profile.company_name, "setting": setting}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorCategoryApiView(APIView):
    """
    Property Evaluator Category
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            property_evaluator_category = PropertyEvaluatorCategory.objects.filter(status=1).order_by("id").values("id", "name")
            return Response(response.parsejson("Fetch data.", property_evaluator_category, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SubdomainPropertyEvaluatorApiView(APIView):
    """
    Subdomain Property Evaluator
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            is_agent = None

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    is_agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))
            agent_list = Users.objects.filter(network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1).order_by("-id").values("id", "first_name", "last_name", "email")
            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(domain=domain_id, status=1)
            if is_agent is not None:
                property_evaluator_domain = property_evaluator_domain.filter(assign_to=user_id)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_listing = property_listing.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_evaluator_domain = property_evaluator_domain.annotate(full_name=Concat('user__first_name', V(' '),'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__email__icontains=search) | Q(user__phone_no__icontains=search))
            total = property_evaluator_domain.count()
            property_evaluator_domain = property_evaluator_domain.order_by("-id").only('id')[offset: limit]
            serializer = SubdomainPropertyEvaluatorSerializer(property_evaluator_domain, many=True)
            all_data = {'total': total, 'data': serializer.data, "agent_list": agent_list}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AssignPropertyEvaluatorApiView(APIView):
    """
    Assign Property Evaluator
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
                    # users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    # if users is None:
                    #     return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "bot_id" in data and data['bot_id'] != "":
                bot_id = int(data['bot_id'])
            else:
                return Response(response.parsejson("bot_id is required.", "", status=403))

            if "assign_to" in data and data['assign_to'] != "":
                assign_to = int(data['assign_to'])
            else:
                return Response(response.parsejson("assign_to is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(id=bot_id, domain=domain_id, status=1).first()
            property_evaluator_domain.assign_to_id = assign_to
            property_evaluator_domain.save()
            return Response(response.parsejson("Assign successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AgentPropertyEvaluatorApiView(APIView):
    """
    Agent Property Evaluator
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(domain=domain_id, assign_to=user_id, status=1)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                # if search.isdigit():
                #     property_listing = property_listing.filter(Q(id=search) | Q(postal_code__icontains=search))
                # else:
                property_evaluator_domain = property_evaluator_domain.annotate(full_name=Concat('user__first_name', V(' '),'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__email__icontains=search) | Q(user__phone_no__icontains=search))
            total = property_evaluator_domain.count()
            property_evaluator_domain = property_evaluator_domain.order_by("-id").only('id')[offset: limit]
            serializer = AgentPropertyEvaluatorSerializer(property_evaluator_domain, many=True)
            all_data = {'total': total, 'data': serializer.data }
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorDetailApiView(APIView):
    """
    Property Evaluator Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            agent_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    agent_id = user_id
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "bot_id" in data and data['bot_id'] != "":
                bot_id = int(data['bot_id'])
            else:
                return Response(response.parsejson("bot_id is required", "", status=403))

            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])
            else:
                return Response(response.parsejson("category_id is required", "", status=403))

            property_evaluator = PropertyEvaluatorUserAnswer.objects.filter(property_evaluator=bot_id, question__category=category_id, property_evaluator__domain=domain_id, property_evaluator__status=1).order_by("question__id")
            if agent_id is not None:
                property_evaluator = property_evaluator.filter(property_evaluator__assign_to=agent_id)
            serializer = PropertyEvaluatorDetailSerializer(property_evaluator, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorStatusChangeApiView(APIView):
    """
    Property Evaluator Status Change
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "bot_id" in data and data['bot_id'] != "":
                bot_id = int(data['bot_id'])
            else:
                return Response(response.parsejson("bot_id is required.", "", status=403))

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(id=bot_id, domain=domain_id, status=1)
            if agent is not None:
                property_evaluator_domain = property_evaluator_domain.filter(assign_to=user_id)
            property_evaluator_domain = property_evaluator_domain.first()
            property_evaluator_domain.complete_status_id = status
            property_evaluator_domain.save()
            return Response(response.parsejson("Status change successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ChangeEvaluatorSettingApiView(APIView):
    """
    Change Evaluator Setting
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_type" in data and type(data['property_type']) == list and len(data['property_type']) > 0:
                property_type = data['property_type']
            else:
                return Response(response.parsejson("property_type is required.", "", status=403))

            PropertyEvaluatorSetting.objects.filter(domain=domain_id).delete()
            for property_type_id in property_type:
                property_evaluator_setting = PropertyEvaluatorSetting()
                property_evaluator_setting.domain_id = domain_id
                property_evaluator_setting.property_type_id = property_type_id
                property_evaluator_setting.status_id = 1
                property_evaluator_setting.save()
            return Response(response.parsejson("Setting change successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyEvaluatorSaveMsgApiView(APIView):
    """
    Property Evaluator Save Msg
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "bot_id" in data and data['bot_id'] != "":
                bot_id = int(data['bot_id'])
            else:
                return Response(response.parsejson("bot_id is required.", "", status=403))

            if "msg" in data and data['msg'] != "":
                msg = data['msg']
            else:
                return Response(response.parsejson("msg is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(id=bot_id, domain=domain_id, status=1)
            if agent is not None:
                property_evaluator_domain = property_evaluator_domain.filter(assign_to=user_id)
            property_evaluator_domain = property_evaluator_domain.first()
            property_evaluator_domain.review_msg = msg
            property_evaluator_domain.save()
            return Response(response.parsejson("Message saved successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class DeleteBotDocApiView(APIView):
    """
    Delete Bot Doc
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "bot_doc_id" in data and data['bot_doc_id'] != "":
                bot_doc_id = int(data['bot_doc_id'])
            else:
                return Response(response.parsejson("bot_doc_id is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(domain=domain_id, user=user_id, status=1).first()
            if property_evaluator_domain is None:
                return Response(response.parsejson("Not authority to delete.", "", status=201))

            PropertyEvaluatorDocAnswer.objects.filter(document=bot_doc_id).delete()
            UserUploads.objects.filter(id=bot_doc_id).delete()
            return Response(response.parsejson("Document delete successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class RebaPropertyListingApiView(APIView):
    """
    Reba property listing
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            property_listing = PropertyListing.objects.filter(is_approved=1, status=1)

            # -----------------Filter-------------------
            if "auction_id" in data and data["auction_id"] != "":
                auction_id = int(data["auction_id"])
                property_listing = property_listing.filter(Q(sale_by_type=auction_id))

            if "property_type" in data and type(data["property_type"]) == list and len(data["property_type"]) > 0:
                property_type = data["property_type"]
                property_listing = property_listing.filter(Q(property_type__in=property_type))

            if "minimum_price" in data and data["minimum_price"] != "":
                minimum_price = int(data["minimum_price"])
                property_listing = property_listing.filter(Q(property_auction__start_price__gte=minimum_price))

            if "maximum_price" in data and data["maximum_price"] != "":
                maximum_price = int(data["maximum_price"])
                property_listing = property_listing.filter(Q(property_auction__start_price__lte=maximum_price))

            if "others" in data and type(data["others"]) == list and len(data["others"]) > 0:
                others = data["others"]
                if len(others) == 2:
                    property_listing = property_listing.filter(Q(broker_co_op=1) | Q(financing_available=1))
                else:
                    if "broker-co-op" in others:
                        property_listing = property_listing.filter(Q(broker_co_op=1))

                    if "financing" in others:
                        property_listing = property_listing.filter(Q(financing_available=1))

            if "agent_id" in data and data["agent_id"] != "":
                agent_id = int(data["agent_id"])
                property_listing = property_listing.filter(Q(agent=agent_id))

            if "asset_id" in data and type(data["asset_id"]) == list and len(data["asset_id"]) > 0:
                asset_id = data["asset_id"]
                property_listing = property_listing.filter(Q(property_asset__in=asset_id))

            if "status" in data and data["status"] != "":
                status = int(data["status"])
                property_listing = property_listing.filter(Q(status=status))

            if "filter" in data and data["filter"] == "auctions_listing":
                property_listing = property_listing.filter(Q(property_auction__start_date__isnull=False) & Q(property_auction__end_date__isnull=False)).exclude(sale_by_type__in=[4, 7])
            elif "filter" in data and data["filter"] == "new_listing":
                min_dt = timezone.now() - timedelta(hours=720)
                # max_dt = timezone.now()
                property_listing = property_listing.filter(added_on__gte=min_dt)
            elif "filter" in data and data["filter"] == "traditional_listing":
                property_listing = property_listing.filter(sale_by_type=4)
            elif "filter" in data and data["filter"] == "recent_sold_listing":
                min_dt = timezone.now() - timedelta(hours=720)
                # max_dt = timezone.now()
                property_listing = property_listing.filter(date_sold__gte=min_dt)
            elif "filter" in data and data["filter"] == "featured":
                property_listing = property_listing.filter(is_featured=1)

            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    property_listing = property_listing.filter(Q(id=search) | Q(postal_code__icontains=search))
                else:
                    property_listing = property_listing.filter(Q(city__icontains=search) |
                                                               Q(state__state_name__icontains=search) |
                                                               Q(address_one__icontains=search) |
                                                               Q(postal_code__icontains=search) |
                                                               Q(property_asset__name__icontains=search) |
                                                               Q(sale_by_type__auction_type__icontains=search))

            # -----------------Sort------------------
            # if "short_by" in data and data["short_by"] != "" and "sort_order" in data and data["sort_order"] != "":
            if "short_by" in data and data["short_by"] != "":
                if data["short_by"].lower() == "auction_start" and data["sort_order"].lower() == "asc":
                    property_listing = property_listing.order_by(F("property_auction__start_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "auction_start" and data["sort_order"].lower() == "desc":
                    property_listing = property_listing.order_by(F("property_auction__start_date").desc(nulls_last=True))
                elif data["short_by"].lower() == "auction_end" and data["sort_order"].lower() == "asc":
                    property_listing = property_listing.order_by(F("property_auction__end_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "auction_end" and data["sort_order"].lower() == "desc":
                    property_listing = property_listing.order_by(F("property_auction__end_date").desc(nulls_last=True))
                elif data["short_by"].lower() == "highest_price":
                    property_listing = property_listing.order_by(F("property_auction__start_price").desc(nulls_last=True))
                elif data["short_by"].lower() == "lowest_price":
                    property_listing = property_listing.order_by(F("property_auction__start_price").asc(nulls_last=True))
                elif data["short_by"].lower() == "page_default":
                    property_listing = property_listing.order_by(F("ordering").asc(nulls_last=True))
                elif data["short_by"].lower() == "ending_soonest":
                    property_listing = property_listing.order_by(F("property_auction__end_date").asc(nulls_last=True))
                elif data["short_by"].lower() == "ending_latest":
                    property_listing = property_listing.order_by(F("property_auction__end_date").desc(nulls_last=True))
            else:
                property_listing = property_listing.order_by("-id")

            total = property_listing.count()
            property_listing = property_listing.only("id")[offset:limit]
            serializer = RebaPropertyListingSerializer(property_listing, many=True, context={"user_id": user_id})
            all_data = {"data": serializer.data, "total": total}
            return Response(response.parsejson("Fetch Data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SaveSearchApiView(APIView):
    """
    Save Search
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            domain_id = None
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))

            agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "name" in data and data["name"] != "":
                name = data["name"]
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            if "parameters" in data and data['parameters'] != "":
                parameters = data['parameters']
            else:
                return Response(response.parsejson("parameters is required.", "", status=403))

            save_search = SaveSearch()
            save_search.domain_id = domain_id
            save_search.name = name
            save_search.parameters = parameters
            save_search.status_id = 1
            save_search.save()
            return Response(response.parsejson("Save search successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class SuperAdminPropertyEvaluatorListApiView(APIView):
    """
    Super Admin Property Evaluator List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "admin_id" in data and data['admin_id'] != "":
                users = Users.objects.filter(id=int(data['admin_id']), status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            property_evaluator_domain = PropertyEvaluatorDomain.objects.filter(status=1)
            if "domain_id" in data and type(data['domain_id']) == list and len(data['domain_id']) > 0:
                property_evaluator_domain = property_evaluator_domain.filter(domain__in=data['domain_id'])
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                property_evaluator_domain = property_evaluator_domain.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__email__icontains=search) | Q(user__phone_no__icontains=search) | Q(domain__users_site_id__user_business_profile__company_name__icontains=search))
            total = property_evaluator_domain.count()
            property_evaluator_domain = property_evaluator_domain.order_by("-id").only('id')[offset: limit]
            serializer = SuperAdminPropertyEvaluatorListSerializer(property_evaluator_domain, many=True)
            all_data = {'total': total, 'data': serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))
        
        
class SuperAdminPropertyEvaluatorDetailApiView(APIView):
    """
    Super Admin Property Evaluator Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "admin_id" in data and data['admin_id'] != "":
                users = Users.objects.filter(id=int(data['admin_id']), status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "bot_id" in data and data['bot_id'] != "":
                bot_id = int(data['bot_id'])
            else:
                return Response(response.parsejson("bot_id is required", "", status=403))

            if "category_id" in data and data['category_id'] != "":
                category_id = int(data['category_id'])
            else:
                return Response(response.parsejson("category_id is required", "", status=403))

            property_evaluator = PropertyEvaluatorUserAnswer.objects.filter(property_evaluator=bot_id, question__category=category_id, property_evaluator__status=1).order_by("question__id")
            serializer = SuperAdminPropertyEvaluatorDetailSerializer(property_evaluator, many=True)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AddPortfolioApiView(APIView):
    """
    Add Portfolio
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "user" in data and data['user'] != "":
                user = int(data['user'])
                users = Users.objects.filter(id=user, site=domain, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user, network_user__domain=domain, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            portfolio_id = None
            if "portfolio_id" in data and data['portfolio_id'] != "":
                portfolio_id = int(data['portfolio_id'])
                portfolio_id = Portfolio.objects.get(id=portfolio_id)

            if "name" in data and data['name'] != "":
                name = data['name']
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            details = None
            if "details" in data and data['details'] != "":
                details = data['details']

            terms = None
            if "terms" in data and data['terms'] != "":
                terms = data['terms']

            contact = None
            if "contact" in data and data['contact'] != "":
                contact = data['contact']

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            property_id = None
            if "property_id" in data and type(data['property_id']) == list and  len(data['property_id'])> 0:
                property_id = data['property_id']

            portfolio_image = None
            if "portfolio_image" in data and type(data['portfolio_image']) == list and len(data['portfolio_image']) > 0:
                portfolio_image = data['portfolio_image']
            
            with transaction.atomic():
                serializer = AddPortfolioSerializer(portfolio_id, data=data)
                if serializer.is_valid():
                    portfolio_id = serializer.save()
                    portfolio_id = portfolio_id.id
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    PropertyPortfolio.objects.filter(portfolio=portfolio_id).delete()
                    if property_id is not None:
                        # PropertyPortfolio.objects.filter(portfolio=portfolio_id).delete()
                        for prop_id in property_id:
                            check_portfolio = PropertyPortfolio.objects.filter(property=prop_id).first()
                            if check_portfolio is None:
                                property_portfolio = PropertyPortfolio()
                                property_portfolio.portfolio_id = portfolio_id
                                property_portfolio.property_id = prop_id
                                property_portfolio.status_id = 1
                                property_portfolio.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                return Response(response.parsejson("Property already in portfolio.", "", status=403))
                    if portfolio_image is not None:
                        PropertyPortfolioImages.objects.filter(portfolio=portfolio_id).delete()
                        for image in portfolio_image:
                            property_portfolio_images = PropertyPortfolioImages()
                            property_portfolio_images.portfolio_id = portfolio_id
                            property_portfolio_images.upload_id = image
                            property_portfolio_images.status_id = 1
                            property_portfolio_images.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Portfolio added successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PortfolioListingApiView(APIView):
    """
    Portfolio Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))
            
            is_agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    is_agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            portfolio = Portfolio.objects.filter(domain=domain_id)
            if is_agent is not None:
                portfolio = portfolio.filter(user=user_id)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                portfolio = portfolio.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(Q(full_name__icontains=search) | Q(user__email__icontains=search) | Q(name__icontains=search))
            total = portfolio.count()
            portfolio = portfolio.order_by("-id").only('id')[offset: limit]
            serializer = PortfolioListingSerializer(portfolio, many=True)
            all_data = {'total': total, 'data': serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PortfolioDetailApiView(APIView):
    """
    Portfolio Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            is_agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1, network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    is_agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "portfolio_id" in data and data['portfolio_id'] != "":
                portfolio_id = int(data['portfolio_id'])
            else:
                return Response(response.parsejson("portfolio_id is required", "", status=403))

            portfolio = Portfolio.objects.filter(id=portfolio_id, domain=domain_id)
            if is_agent is not None:
                portfolio = portfolio.filter(user=user_id)
                
            portfolio = portfolio.first()
            serializer = PortfolioDetailSerializer(portfolio)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PortfolioDeleteImageApiView(APIView):
    """
    Portfolio Delete Image
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            is_agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1,
                                                 network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    is_agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "upload_id" in data and data['upload_id'] != "":
                upload_id = int(data['upload_id'])
            else:
                return Response(response.parsejson("upload_id is required", "", status=403))

            PropertyPortfolioImages.objects.filter(upload=upload_id, portfolio__domain=domain_id).delete()
            UserUploads.objects.filter(id=upload_id).delete()
            return Response(response.parsejson("Image deleted successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PortfolioPropertyListApiView(APIView):
    """
    Portfolio Property List
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
                network = NetworkDomain.objects.filter(id=domain_id, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            is_agent = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=domain_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=domain_id, network_user__status=1,
                                                 network_user__is_agent=1, status=1, user_type__in=[1, 2]).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
                    is_agent = True
            else:
                return Response(response.parsejson("user_id is required.", "", status=403))

            portfolio_id = None
            if "portfolio_id" in data and data['portfolio_id'] != "":
                portfolio_id = int(data['portfolio_id'])
            if portfolio_id is None:
                data = PropertyListing.objects.annotate(p_count=Count("property_portfolio_property__portfolio")).filter(domain=domain_id, sale_by_type=1, property_asset=1, p_count__lt=1, status=1)
            else:
                data = PropertyListing.objects.annotate(p_count=Count("property_portfolio_property__portfolio", filter=~Q(property_portfolio_property__portfolio__id=portfolio_id))).filter(domain=domain_id, sale_by_type=1, property_asset=1, p_count__lt=1, status=1)
            if is_agent is not None:
                data = data.filter(agent=user_id)
            data = data.values('id', 'address_one', 'address_two', 'city', 'postal_code', state_name=F('state__state_name'))
            return Response(response.parsejson("Fetch data.", data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTotalViewApiView(APIView):
    """
    Property total view
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            property_detail = PropertyListing.objects.get(Q(id=property_id) & Q(domain=site_id))
            property_detail = ViewCountPropertyDetailSerializer(property_detail)

            view_data = PropertyView.objects.filter(domain=site_id, property=property_id)
            if "search" in data and data['search'] != "":
                view_data = view_data.annotate(full_name=Concat('user__first_name', V(' '),'user__last_name')).filter(Q(full_name__icontains=data['search']) | Q(user__email__icontains=data['search']) | Q(user__phone_no__icontains=data['search']))
            total = view_data.count()
            view_data = view_data.order_by("-id").only("id")[offset:limit]
            serializer = PropertyVewCountDetailSerializer(view_data, many=True)
            all_data = {"property_detail": property_detail.data, "data": serializer.data, "total": total}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class PropertyTotalWatcherApiView(APIView):
    """
    Property total watcher
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data

            if "site_id" in data and data['site_id'] != "":
                site_id = int(data['site_id'])
                network = NetworkDomain.objects.filter(id=site_id, is_active=1).first()
                if network is None:
                    # Translators: This message appears when site not exist
                    return Response(response.parsejson("Site not exist.", "", status=403))
            else:
                # Translators: This message appears when site_id is empty
                return Response(response.parsejson("site_id is required.", "", status=403))

            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                users = Users.objects.filter(id=user_id, site=site_id, user_type=2, status=1).first()
                if users is None:
                    users = Users.objects.filter(id=user_id, network_user__domain=site_id, network_user__is_agent=1, network_user__status=1, status=1, user_type=2).first()
                    if users is None:
                        return Response(response.parsejson("User not exist.", "", status=403))
            else:
                # Translators: This message appears when user_id is empty
                return Response(response.parsejson("user_id is required.", "", status=403))

            if "property_id" in data and data['property_id'] != "":
                property_id = int(data['property_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("property_id is required", "", status=403))

            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            property_detail = PropertyListing.objects.get(Q(id=property_id) & Q(domain=site_id))
            property_detail = ViewCountPropertyDetailSerializer(property_detail)

            watcher_data = PropertyWatcher.objects.filter(property__domain=site_id, property=property_id)
            if "search" in data and data['search'] != "":
                watcher_data = watcher_data.annotate(full_name=Concat('user__first_name', V(' '),'user__last_name')).filter(Q(full_name__icontains=data['search']) | Q(user__email__icontains=data['search']) | Q(user__phone_no__icontains=data['search']))
            total = watcher_data.count()
            watcher_data = watcher_data.order_by("-id").only("id")[offset:limit]
            serializer = PropertyWatcherCountDetailSerializer(watcher_data, many=True)
            all_data = {"property_detail": property_detail.data, "data": serializer.data, "total": total}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class ParcelDetailApiView(APIView):
    """
    Parcel Detail
    """
    authentication_classes = [OAuth2Authentication, TokenAuthentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "domain_id" in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", "", status=403))

            user_id = None
            if "user_id" in data and data['user_id'] != "":
                user_id = int(data['user_id'])

            if "parcel_id" in data and data['parcel_id'] != "":
                parcel_id = int(data['parcel_id'])
            else:
                # Translators: This message appears when property_id is empty
                return Response(response.parsejson("parcel_id is required", "", status=403))

            total_portfolio = PropertyPortfolio.objects.filter(portfolio__domain=domain_id, portfolio=parcel_id, status=1)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                if search.isdigit():
                    total_portfolio = total_portfolio.filter(Q(id=search) | Q(property__postal_code__icontains=search))
                else:
                    total_portfolio = total_portfolio.annotate(property_name=Concat('property__address_one', V(', '), 'property__city', V(', '), 'property__state__state_name', V(' '), 'property__postal_code', output_field=CharField())).filter(Q(property__city__icontains=search) | Q(property__state__state_name__icontains=search) | Q(property__address_one__icontains=search) | Q(property__postal_code__icontains=search) | Q(property__property_asset__name__icontains=search) | Q(property__sale_by_type__auction_type__icontains=search) | Q(property_name__icontains=search))
            total = total_portfolio.count()
            total_portfolio = total_portfolio.order_by("-id").only("id")[offset:limit]
            serializer = ParcelDetailSerializer(total_portfolio, many=True, context=user_id)
            portfolio = Portfolio.objects.filter(domain=domain_id, id=parcel_id, status=1).first()
            portfolio_detail = {"name": portfolio.name, "details": portfolio.details, "terms": portfolio.terms, "contact": portfolio.contact}
            all_data = {"data": serializer.data, "total": total, "portfolio_detail": portfolio_detail}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPortfolioListingApiView(APIView):
    """
    Admin Portfolio Listing
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            offset = 0
            if 'page_size' in data and data['page_size'] != "":
                limit = int(data['page_size'])
            else:
                limit = int(settings.LIST_PER_PAGE)

            if 'page' in data and data['page'] != "":
                page = int(data['page'])
            else:
                page = 1
            # -----------Set Pagination Value--------
            if limit > 0:
                offset = (page - 1) * limit
                limit = limit * page

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            domain = None
            if "domain" in data and len(data['domain']) > 0 and type(data['domain']) == list:
                domain = data['domain']

            portfolio = Portfolio.objects.filter(status=1)
            if domain is not None:
                portfolio = portfolio.filter(domain__in=domain)
            # -----------------Search-------------------
            if 'search' in data and data['search'] != "":
                search = data['search'].strip()
                portfolio = portfolio.annotate(full_name=Concat('user__first_name', V(' '), 'user__last_name')).filter(
                    Q(full_name__icontains=search) | Q(user__email__icontains=search) | Q(name__icontains=search))
            total = portfolio.count()
            portfolio = portfolio.order_by("-id").only('id')[offset: limit]
            serializer = AdminPortfolioListingSerializer(portfolio, many=True)
            all_data = {'total': total, 'data': serializer.data}
            return Response(response.parsejson("Fetch data.", all_data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminAddPortfolioApiView(APIView):
    """
    Admin Add Portfolio
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "domain" in data and data['domain'] != "":
                domain = int(data['domain'])
                network = NetworkDomain.objects.filter(id=domain, is_active=1).first()
                if network is None:
                    return Response(response.parsejson("Site not exist.", "", status=403))
                users = Users.objects.filter(site=domain, user_type=2, status=1).first()
                if users is None:
                    return Response(response.parsejson("No broker account exist.", "", status=403))
                data['user'] = users.id
            else:
                return Response(response.parsejson("domain is required", "", status=403))

            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            portfolio_id = None
            if "portfolio_id" in data and data['portfolio_id'] != "":
                portfolio_id = int(data['portfolio_id'])
                portfolio_id = Portfolio.objects.get(id=portfolio_id)

            if "name" in data and data['name'] != "":
                name = data['name']
            else:
                return Response(response.parsejson("name is required.", "", status=403))

            details = None
            if "details" in data and data['details'] != "":
                details = data['details']

            terms = None
            if "terms" in data and data['terms'] != "":
                terms = data['terms']

            contact = None
            if "contact" in data and data['contact'] != "":
                contact = data['contact']

            if "status" in data and data['status'] != "":
                status = int(data['status'])
            else:
                return Response(response.parsejson("status is required.", "", status=403))

            property_id = None
            if "property_id" in data and type(data['property_id']) == list and len(data['property_id']) > 0:
                property_id = data['property_id']

            portfolio_image = None
            if "portfolio_image" in data and type(data['portfolio_image']) == list and len(data['portfolio_image']) > 0:
                portfolio_image = data['portfolio_image']

            with transaction.atomic():
                serializer = AddPortfolioSerializer(portfolio_id, data=data)
                if serializer.is_valid():
                    portfolio_id = serializer.save()
                    portfolio_id = portfolio_id.id
                else:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    copy_errors = serializer.errors.copy()
                    return Response(response.parsejson(copy_errors, "", status=403))
                try:
                    PropertyPortfolio.objects.filter(portfolio=portfolio_id).delete()
                    if property_id is not None:
                        # PropertyPortfolio.objects.filter(portfolio=portfolio_id).delete()
                        for prop_id in property_id:
                            check_portfolio = PropertyPortfolio.objects.filter(property=prop_id).first()
                            if check_portfolio is None:
                                property_portfolio = PropertyPortfolio()
                                property_portfolio.portfolio_id = portfolio_id
                                property_portfolio.property_id = prop_id
                                property_portfolio.status_id = 1
                                property_portfolio.save()
                            else:
                                transaction.set_rollback(True)  # -----Rollback Transaction----
                                return Response(response.parsejson("Property already in portfolio.", "", status=403))
                    if portfolio_image is not None:
                        PropertyPortfolioImages.objects.filter(portfolio=portfolio_id).delete()
                        for image in portfolio_image:
                            property_portfolio_images = PropertyPortfolioImages()
                            property_portfolio_images.portfolio_id = portfolio_id
                            property_portfolio_images.upload_id = image
                            property_portfolio_images.status_id = 1
                            property_portfolio_images.save()
                except Exception as exp:
                    transaction.set_rollback(True)  # -----Rollback Transaction----
                    return Response(response.parsejson(str(exp), exp, status=403))
            return Response(response.parsejson("Portfolio added successfully.", "", status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class AdminPortfolioDetailApiView(APIView):
    """
    Admin Portfolio Detail
    """
    authentication_classes = [OAuth2Authentication]

    @staticmethod
    def post(request):
        try:
            data = request.data
            if "admin_id" in data and data['admin_id'] != "":
                admin_id = int(data['admin_id'])
                users = Users.objects.filter(id=admin_id, user_type=3, status=1).first()
                if users is None:
                    return Response(response.parsejson("User not exist.", "", status=403))
            else:
                return Response(response.parsejson("admin_id is required.", "", status=403))

            if "portfolio_id" in data and data['portfolio_id'] != "":
                portfolio_id = int(data['portfolio_id'])
            else:
                return Response(response.parsejson("portfolio_id is required", "", status=403))

            portfolio = Portfolio.objects.filter(id=portfolio_id)

            portfolio = portfolio.first()
            serializer = AdminPortfolioDetailSerializer(portfolio)
            return Response(response.parsejson("Fetch data.", serializer.data, status=201))
        except Exception as exp:
            return Response(response.parsejson(str(exp), exp, status=403))


class BulkPropertyUploadApiView(APIView):
    """ This is BulkPropertyUploadApiView class

    """
    authentication_classes = [TokenAuthentication, OAuth2Authentication]

    def post(self, request):
        try:
            data = request.data
            if 'domain_id' in data and data['domain_id'] != "":
                domain_id = int(data['domain_id'])
            else:
                return Response(response.parsejson("domain_id is required", '', status=403))

            if 'user_id' in data and data['user_id'] != "":
                user_id = int(data['user_id'])
                try:
                    Users.objects.get(id=user_id, user_type=2, status=1)
                except Exception as exp:
                    return Response(response.parsejson("Not valid user", '', status=403))
            else:
                return Response(response.parsejson("user_id is required", '', status=403))

            if 'csv_url' in data and data['csv_url'] != "":
                csv_url = data['csv_url']
            else:
                return Response(response.parsejson("csv_url is required", '', status=403))
            # csv_url = 'https://new-realtyonegroup.s3.us-west-1.amazonaws.com/property_image/1699522753.052704_sample.csv'
            csv_data = pd.read_csv(csv_url)
            csv_data = csv_data.fillna('')
            column_names = list(csv_data.columns.values)
            # ------------Check Heading-------------
            chk_heading = check_csv_heading(column_names)  # CSV Checking Method Call
            if chk_heading == 'notMatch':  # Checking csv heading
                return Response(response.parsejson("Invalid heading", "", status=404))

            # ------------Check Data Type-------------
            data_validation = csv_data_validation(csv_data)
            if type(data_validation) is not list:
                return Response(response.parsejson(str(data_validation), "", status=404))

            # ------------Property Data Entry-------------
            for items in data_validation:
                with transaction.atomic():
                    try:
                        # ---------------------Add Property--------------
                        listing_data = {
                            'domain': domain_id,
                            'agent': user_id,
                            'is_approved': 1,
                            'status': 1,
                            'title': 'Testing',
                            'property_asset': items['property_asset_id'] if 'property_asset_id' in items else None,
                            'property_type': items['property_type_id'] if 'property_type_id' in items else None,
                            # 'property_type': items['subtype'] if 'subtype_id' in items else None
                            'beds': items['beds'] if 'beds' in items else None,
                            'baths': items['baths'] if 'baths' in items else None,
                            'square_footage': items['square_footage'] if 'square_footage' in items else None,
                            'year_built': items['year_built'] if 'year_built' in items else None,
                            'country': items['country_id'] if 'country_id' in items else None,
                            'address_one': items['address_one'] if 'address_one' in items else None,
                            'postal_code': items['postal_code'] if 'postal_code' in items else None,
                            'city': items['city'] if 'city' in items else None,
                            'state': items['state_id'] if 'state_id' in items else None,
                            'sale_by_type': items['sale_by_type_id'] if 'sale_by_type_id' in items else None,
                            'is_featured': items['is_featured'] if 'is_featured' in items else None,
                            'buyers_premium': items['buyers_premium'] if 'buyers_premium' in items else 0,
                            'buyers_premium_percentage': items['buyers_premium_percentage'] if 'buyers_premium_percentage' in items else None,
                            'buyers_premium_min_amount': items['buyers_premium_min_amount'] if 'buyers_premium_min_amount' in items else None,
                            'description': items['description'] if 'description' in items else None,
                            'sale_terms': items['sale_terms'] if 'sale_terms' in items else None,
                            'due_diligence_period': items['due_diligence_period'] if 'due_diligence_period' in items else None,
                            'escrow_period': items['escrow_period'] if 'escrow_period' in items else None,
                            'highest_best_format': items['highest_best_format'] if 'highest_best_format' in items else 3,
                            'auction_location': items['auction_location'] if 'auction_location' in items else None,
                            'total_acres': items['total_acres'] if 'total_acres' in items else None,
                        }

                        serializer = AddBulkPropertySerializer(data=listing_data)
                        if serializer.is_valid():
                            property_id = serializer.save()
                            property_id = property_id.id
                            print(property_id)

                        else:
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                        auction_data = {
                            'domain': domain_id,
                            'property': property_id,
                            'start_date': items['bidding_starting_time'] if 'bidding_starting_time' in items else None,
                            'end_date': items['bidding_ending_time'] if 'bidding_ending_time' in items else None,
                            'reserve_amount': items['reserve_amount'] if 'reserve_amount' in items else None,
                            'bid_increments': items['bid_increments'] if 'bid_increments' in items else None,
                            'status': 1,
                            'start_price': items['bidding_min_price'] if 'bidding_min_price' in items else None,
                            'open_house_start_date': items['open_house_start_date'] if 'open_house_start_date' in items else None,
                            'open_house_end_date': items['open_house_end_date'] if 'open_house_end_date' in items else None,
                            'offer_amount': items['bidding_min_price'] if 'bidding_min_price' in items else None,
                            'auction': items['sale_by_type_id'] if 'sale_by_type_id' in items else None,
                        }
                        # print(property_id)
                        # print(auction_data)
                        serializer = AddBulkAuctionSerializer(data=auction_data)
                        if serializer.is_valid():
                            auction_id = serializer.save()
                            auction_id = auction_id.id
                        else:
                            copy_errors = serializer.errors.copy()
                            return Response(response.parsejson(copy_errors, "", status=403))

                        # ------------------PropertySubtype---------------
                        if 'subtype_id' in items and type(items['subtype_id']) == int and items['subtype_id'] > 0:
                            property_subtype = PropertySubtype()
                            property_subtype.property_id = property_id
                            property_subtype.subtype_id = items['subtype_id']
                            property_subtype.save()
                    except Exception as exp:
                        transaction.set_rollback(True)  # -----Rollback Transaction----
                        return Response(response.parsejson(str(exp), exp, status=403))

            return Response(response.parsejson("success", "", status=201))
        except Exception as exp:
            return Response(response.parsejson("Unable to process", "", status=403))


class PropertyTypeApiView(APIView):
    """ This is PropertyTypeApiView class

    """
    authentication_classes = [TokenAuthentication, OAuth2Authentication]

    def post(self, request):
        try:
            data = request.data
            if 'asset_id' in data and data['asset_id'] != "":
                asset_id = int(data['asset_id'])
            else:
                asset_id = None

            property_type = LookupPropertyType.objects
            if asset_id is not None:
                property_type = property_type.filter(asset=asset_id, is_active=1)
            else:
                property_type = property_type.filter(is_active=1) 

            property_type = property_type.order_by("-id").values("id", "property_type")      
            return Response(response.parsejson("Fetch data", property_type, status=201))
        except Exception as exp:
            return Response(response.parsejson("Unable to process", "", status=403))        
