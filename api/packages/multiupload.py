import base64
from random import randint
import re
from api.users.models import *
import uuid
from django.conf import settings
from django.core.cache import cache
from api.packages.constants import *
from django.db.models.functions import Lower, Trim
import numpy as np
from django.core.cache.backends.base import DEFAULT_TIMEOUT
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


def b64encode_old(source):
    source = "xsd0xa" + source + "xsd1xa"
    source = source.encode('utf-8')
    content = base64.b64encode(source).decode('utf-8')
    return content


def check_csv_heading(csv_heading):
    """Csv heading check method

    """
    try:
        if len(PROPERTY_CSV_HEADING) == len(csv_heading):
            for head in range(len(PROPERTY_CSV_HEADING)):
                if PROPERTY_CSV_HEADING[head].lower().strip() != csv_heading[head].lower().strip():
                    return "notMatch"
        else:
            return "notMatch"
    except Exception as e:
        return "notMatch"


def csv_data_validation(df):
    """Validate property data

    """
    try:
        row_count = len(df.index)
        data = []
        response_type = ""
        for row in range(0, row_count):
            row_data = {}
            # ------------Asset Type-------------
            asset_type_id = get_asset_type_id(df['Asset Type'][row])
            if asset_type_id == "error":
                response_type = "Error in Asset Type"
                break
            row_data['property_asset_id'] = asset_type_id

            # -------------------Property Features-------------------
            if asset_type_id == 1:  # ---Lands/Lots
                row_data['property_asset_id'] = asset_type_id
                # ------------Total Acres-------------
                if not np.issubdtype(type(df['Total Acres'][row]), int):
                    response_type = "Error in Total Acres"
                    break
                row_data['total_acres'] = int(df['Total Acres'][row])
            elif asset_type_id == 2:  # ---Commercial
                row_data['property_asset_id'] = asset_type_id
            elif asset_type_id == 3:  # ---Residential
                # ------------Check Property Type-------------
                property_type_id = get_property_type_id(df['Property Type'][row], asset_type_id)
                if property_type_id == "error":
                    response_type = "Error in Property Type"
                    break
                row_data['property_type_id'] = property_type_id

                # ------------Check Property Sub Type-------------
                subtype_id = get_property_subtype_id(df['Property Sub Type'][row], asset_type_id)
                if subtype_id == "error":
                    response_type = "Error in Property Sub Type"
                    break
                row_data['subtype_id'] = subtype_id

                # ------------Check Beds-------------
                if not np.issubdtype(type(df['Beds'][row]), int):
                    response_type = "Error in Beds"
                    break
                row_data['beds'] = int(df['Beds'][row])

                # ------------Check Baths-------------
                if not np.issubdtype(type(df['Baths'][row]), int):
                    response_type = "Error in Baths"
                    break
                row_data['baths'] = int(df['Baths'][row])

                # ------------Square Footage-------------
                if not np.issubdtype(type(df['Square Footage'][row]), int):
                    response_type = "Error in Square Footage"
                    break
                row_data['square_footage'] = int(df['Square Footage'][row])

                # ------------Year Built-------------
                if not np.issubdtype(type(df['Year Built'][row]), int):
                    response_type = "Error in Year Built"
                    break
                row_data['year_built'] = int(df['Year Built'][row])
            # -------------------Property General/Bidding Information-------------------

            # -------------------Check Country------------------
            country_id = get_country_id(df['Country'][row])
            if country_id == "error":
                response_type = "Error in Country"
                break
            row_data['country_id'] = country_id

            # ------------Address-------------
            if df['Address'][row] == "":
                response_type = "Error in Address"
                break
            row_data['address_one'] = df['Address'][row]

            # ------------Zipcode-------------
            if not np.issubdtype(type(df['Zip Code'][row]), int):
                response_type = "Error in Zip Code"
                break
            row_data['postal_code'] = int(df['Zip Code'][row])

            # ------------City-------------
            if df['City'][row] == "":
                response_type = "Error in City"
                break
            row_data['city'] = df['City'][row]

            # -------------------Check State------------------
            state_id = get_state_id(df['State'][row], country_id)
            if state_id == "error":
                response_type = "Error in State"
                break
            row_data['state_id'] = state_id

            # -------------------Auction Type------------------
            sale_by_type_id = get_auction_type_id(df['Auction Type'][row])
            if state_id == "error":
                response_type = "Error in Auction Type"
                break
            row_data['sale_by_type_id'] = sale_by_type_id

            if sale_by_type_id == 1:  # Classic Auction
                # ------------Bidding Starting Time-------------
                if df['Bidding Starting Time'][row] == "":
                    response_type = "Error in Bidding Starting Time"
                    break
                row_data['bidding_starting_time'] = df['Bidding Starting Time'][row]

                # ------------Bidding Ending Time-------------
                if df['Bidding Ending Time'][row] == "":
                    response_type = "Error in Bidding Ending Time"
                    break
                row_data['bidding_ending_time'] = df['Bidding Ending Time'][row]

                # ------------Open House Start Date-------------
                if df['Open House Start Date'][row] == "":
                    response_type = "Error in Open House Start Date"
                    break
                row_data['open_house_start_date'] = df['Open House Start Date'][row]

                # ------------Open House End Date-------------
                if df['Open House End Date'][row] == "":
                    response_type = "Error in Open House End Date"
                    break
                row_data['open_house_end_date'] = df['Open House End Date'][row]

                # ------------Bid Minimum Price-------------
                if df['Bid Minimum Price'][row] == "" or not np.issubdtype(type(df['Bid Minimum Price'][row]), int):
                    response_type = "Error in Bid Minimum Price"
                    break
                row_data['bidding_min_price'] = int(df['Bid Minimum Price'][row])

                # ------------Reserve Amount-------------
                if df['Reserve Amount'][row] == "" or not np.issubdtype(type(df['Reserve Amount'][row]), int):
                    response_type = "Error in Reserve Amount"
                    break
                else:
                    if int(df['Reserve Amount'][row]) <= int(df['Bid Minimum Price'][row]):
                        response_type = "Error in Reserve Amount"
                        break
                row_data['reserve_amount'] = int(df['Reserve Amount'][row])

                # ------------Bid Increments-------------
                if df['Bid Increments'][row] == "" or not np.issubdtype(type(df['Bid Increments'][row]), int):
                    response_type = "Error in Bid Increments"
                    break
                row_data['bid_increments'] = df['Bid Increments'][row]

                # ------------Is Featured Listing-------------
                if df['Is Featured Listing'][row] == "":
                    row_data['is_featured'] = False
                elif df['Is Featured Listing'][row].lower() == "yes":
                    row_data['is_featured'] = True
                elif df['Is Featured Listing'][row].lower() == "no":
                    row_data['is_featured'] = False
                else:
                    response_type = "Error in Featured Listing"
                    break

                # ------------Buyers Premium-------------
                if df['Buyers Premium'][row] == "":
                    response_type = "Error in Bid Increments"
                elif df['Buyers Premium'][row].lower() == "yes":
                    row_data['buyers_premium'] = True
                elif df['Buyers Premium'][row].lower() == "no":
                    row_data['buyers_premium'] = False
                else:
                    response_type = "Error in Buyers Premium"
                    break

                # ------------Buyers Premium %-------------
                if df['Buyers Premium'][row].lower() == "yes":
                    if df['Buyers Premium %'][row] == "" or not np.issubdtype(type(df['Buyers Premium %'][row]), int):
                        response_type = "Error in Buyers Premium %"
                        break
                    else:
                        row_data['buyers_premium_percentage'] = int(df['Buyers Premium %'][row])

                # ------------Buyers Premium Minimum Amount-------------
                if df['Buyers Premium'][row].lower() == "yes":
                    if df['Buyers Premium Minimum Amount'][row] != "" or np.issubdtype(type(df['Buyers Premium Minimum Amount'][row]), int):
                        row_data['buyers_premium_min_amount'] = int(df['Buyers Premium Minimum Amount'][row])

            elif sale_by_type_id == 7:  # Highest and Best
                # ------------Offer Starting Time-------------
                if df['Offer Starting Time'][row] == "":
                    response_type = "Error in Offer Starting Time"
                    break
                row_data['bidding_starting_time'] = df['Offer Starting Time'][row]

                # ------------Offer Ending Time-------------
                if df['Offer Ending Time'][row] == "":
                    response_type = "Error in Offer Ending Time"
                    break
                row_data['bidding_ending_time'] = df['Offer Ending Time'][row]

                # ------------Open House Start Date-------------
                if df['Open House Start Date'][row] == "":
                    response_type = "Error in Open House Start Date"
                    break
                row_data['open_house_start_date'] = df['Open House Start Date'][row]

                # ------------Open House End Date-------------
                if df['Open House End Date'][row] == "":
                    response_type = "Error in Open House End Date"
                    break
                row_data['open_house_end_date'] = df['Open House End Date'][row]

                # ------------Asking Price-------------
                if df['Asking Price'][row] == "" or not np.issubdtype(type(df['Asking Price'][row]), int):
                    response_type = "Error in Asking Price"
                    break
                row_data['bidding_min_price'] = int(df['Asking Price'][row])

                # ------------Due Diligence Period-------------
                if df['Due Diligence Period'][row] == "" or not np.issubdtype(type(df['Due Diligence Period'][row]), int):
                    response_type = "Error in Due Diligence Period"
                    break
                row_data['due_diligence_period'] = int(df['Due Diligence Period'][row])

                # ------------Escrow Period-------------
                if df['Escrow Period'][row] == "" or not np.issubdtype(type(df['Escrow Period'][row]), int):
                    response_type = "Error in Escrow Period"
                    break
                row_data['escrow_period'] = int(df['Escrow Period'][row])

                # ------------Highest and Best Auction Format-------------
                highest_and_best_auction_format = get_highest_and_best_auction_format_id(df['Highest and Best Auction Format'][row])
                if highest_and_best_auction_format == "error":
                    response_type = "Error in Highest and Best Auction Format"
                    break
                row_data['highest_best_format'] = highest_and_best_auction_format

                # ------------Is Featured Listing-------------
                if df['Is Featured Listing'][row] == "":
                    row_data['is_featured'] = False
                elif df['Is Featured Listing'][row].lower() == "yes":
                    row_data['is_featured'] = True
                elif df['Is Featured Listing'][row].lower() == "no":
                    row_data['is_featured'] = False
                else:
                    response_type = "Error in Featured Listing"
                    break

                # ------------Buyers Premium-------------
                if df['Buyers Premium'][row] == "":
                    response_type = "Error in Bid Increments"
                elif df['Buyers Premium'][row].lower() == "yes":
                    row_data['buyers_premium'] = True
                elif df['Buyers Premium'][row].lower() == "no":
                    row_data['buyers_premium'] = False
                else:
                    response_type = "Error in Buyers Premium"
                    break

                # ------------Buyers Premium %-------------
                if df['Buyers Premium'][row].lower() == "yes":
                    if df['Buyers Premium %'][row] == "" or not np.issubdtype(type(df['Buyers Premium %'][row]), int):
                        response_type = "Error in Buyers Premium %"
                        break
                    else:
                        row_data['buyers_premium_percentage'] = int(df['Buyers Premium %'][row])

                # ------------Buyers Premium Minimum Amount-------------
                if df['Buyers Premium'][row].lower() == "yes":
                    if df['Buyers Premium Minimum Amount'][row] != "" or np.issubdtype(
                            type(df['Buyers Premium Minimum Amount'][row]), int):
                        row_data['buyers_premium_min_amount'] = int(df['Buyers Premium Minimum Amount'][row])
            elif sale_by_type_id == 6:  # Live Event Auction
                # ------------Bidding Starting Time-------------
                if df['Bidding Starting Time'][row] == "":
                    response_type = "Error in Bidding Starting Time"
                    break
                row_data['bidding_starting_time'] = df['Bidding Starting Time'][row]

                # ------------Bidding Ending Time-------------
                if df['Bidding Ending Time'][row] == "":
                    response_type = "Error in Bidding Ending Time"
                    break
                row_data['bidding_ending_time'] = df['Bidding Ending Time'][row]

                # ------------Open House Start Date-------------
                if df['Open House Start Date'][row] == "":
                    response_type = "Error in Open House Start Date"
                    break
                row_data['open_house_start_date'] = df['Open House Start Date'][row]

                # ------------Open House End Date-------------
                if df['Open House End Date'][row] == "":
                    response_type = "Error in Open House End Date"
                    break
                row_data['open_house_end_date'] = df['Open House End Date'][row]

                # ------------Auction Location-------------
                if df['Auction Location'][row] == "":
                    response_type = "Error in Auction Location"
                    break
                row_data['auction_location'] = df['Auction Location'][row]

                # ------------Bid Minimum Price-------------
                if df['Bid Minimum Price'][row] == "" or not np.issubdtype(type(df['Bid Minimum Price'][row]), int):
                    response_type = "Error in Bid Minimum Price"
                    break
                row_data['bidding_min_price'] = int(df['Bid Minimum Price'][row])

                # ------------Reserve Amount-------------
                if df['Reserve Amount'][row] == "" or not np.issubdtype(type(df['Reserve Amount'][row]), int):
                    response_type = "Error in Reserve Amount"
                    break
                else:
                    if int(df['Reserve Amount'][row]) <= int(df['Bid Minimum Price'][row]):
                        response_type = "Error in Reserve Amount"
                        break
                row_data['reserve_amount'] = int(df['Reserve Amount'][row])

                # ------------Is Featured Listing-------------
                if df['Is Featured Listing'][row] == "":
                    row_data['is_featured'] = False
                elif df['Is Featured Listing'][row].lower() == "yes":
                    row_data['is_featured'] = True
                elif df['Is Featured Listing'][row].lower() == "no":
                    row_data['is_featured'] = False
                else:
                    response_type = "Error in Featured Listing"
                    break
            elif sale_by_type_id == 4:  # Traditional Listing
                # ------------Open House Start Date-------------
                if df['Open House Start Date'][row] == "":
                    response_type = "Error in Open House Start Date"
                    break
                row_data['open_house_start_date'] = df['Open House Start Date'][row]

                # ------------Open House End Date-------------
                if df['Open House End Date'][row] == "":
                    response_type = "Error in Open House End Date"
                    break
                row_data['open_house_end_date'] = df['Open House End Date'][row]

                # ------------Asking Price-------------
                if df['Asking Price'][row] == "" or not np.issubdtype(type(df['Asking Price'][row]), int):
                    response_type = "Error in Asking Price"
                    break
                row_data['bidding_min_price'] = int(df['Asking Price'][row])

                # ------------Is Featured Listing-------------
                if df['Is Featured Listing'][row] == "":
                    row_data['is_featured'] = False
                elif df['Is Featured Listing'][row].lower() == "yes":
                    row_data['is_featured'] = True
                elif df['Is Featured Listing'][row].lower() == "no":
                    row_data['is_featured'] = False
                else:
                    response_type = "Error in Featured Listing"
                    break

            # ------------About Property-------------
            if df['About Property'][row] != "":
                row_data['description'] = df['About Property'][row]

            # ------------Terms of Sale-------------
            if df['Terms of Sale'][row] != "":
                row_data['sale_terms'] = df['Terms of Sale'][row]

            data.append(row_data)
        if response_type:
            return response_type
        else:
            return data
    except Exception as exp:
        print(exp)
        return 'error'


def get_asset_type_id(data):
    try:
        data = data.strip().lower()
        response = LookupPropertyAsset.objects.annotate(search=Lower(Trim('name'))).get(search=data)
        return response.id
    except Exception as exp:
        return "error"


def get_property_type_id(data, asset_type_id):
    try:
        data = data.strip().lower()
        response = LookupPropertyType.objects.annotate(search=Lower(Trim('property_type'))).get(search=data, asset=asset_type_id)
        return response.id
    except Exception as exp:
        return "error"


def get_property_subtype_id(data, asset_type_id):
    try:
        data = data.strip().lower()
        if data:
            response = LookupPropertySubType.objects.annotate(search=Lower(Trim('name'))).get(search=data, asset=asset_type_id)
            return response.id
        else:
            return ""
    except Exception as exp:
        return "error"


def get_country_id(data):
    try:
        data = data.strip().lower()
        response = LookupCountry.objects.annotate(search=Lower(Trim('country_name'))).get(search=data)
        return response.id
    except Exception as exp:
        return "error"


def get_state_id(data, country_id):
    try:
        data = data.strip().lower()
        response = LookupState.objects.annotate(search=Lower(Trim('state_name'))).get(search=data, country=country_id)
        return response.id
    except Exception as exp:
        return "error"


def get_auction_type_id(data):
    try:
        data = data.strip().lower()
        response = LookupAuctionType.objects.annotate(search=Lower(Trim('auction_type'))).get(search=data, is_active=True)
        return response.id
    except Exception as exp:
        return "error"


def get_highest_and_best_auction_format_id(data):
    try:
        data = data.strip().lower()
        auction_format_id = None
        if data == 'private':
            auction_format_id = 2
        elif data == 'public':
            auction_format_id = 3
        if auction_format_id is None:
            return "error"
        else:
            return auction_format_id
    except Exception as exp:
        return "error"