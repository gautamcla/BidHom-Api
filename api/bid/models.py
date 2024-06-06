from django.db import models
from api.property.models import *


class Default(models.Model):
    """This abstract class for common field

    """
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bid'
        abstract = True


class BidRegistration(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="bid_registration_domain", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="bid_registration_property", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="bid_registration_user", on_delete=models.CASCADE, null=True, blank=True)
    registration_id = models.CharField(max_length=20, null=True, blank=True, unique=True)
    is_reviewed = models.BooleanField(default=0)
    is_approved = models.IntegerField(choices=((1, "Pending"), (2, "Approved"), (3, "Declined"), (4, "Not Interested")), default=1)
    term_accepted = models.BooleanField(default=1)
    age_accepted = models.BooleanField(default=1)
    correct_info = models.BooleanField(default=1)
    user_type = models.IntegerField(choices=((1, "Investor"), (2, "Buyer"), (3, "Seller"), (4, "Agent")), default=2)
    buyer_comment = models.TextField(null=True, blank=True)
    seller_comment = models.TextField(null=True, blank=True)
    ip_address = models.CharField(max_length=20, null=True, blank=True)
    working_with_agent = models.BooleanField(default=0)
    property_yourself = models.BooleanField(default=0)
    upload_pof = models.BooleanField(default=0)
    reason_for_not_upload = models.IntegerField(choices=((1, "Currently Working With My Lender To Obtain Financing"), (2, "Put Me In Contact With Lender(s) To Obtain Financing"), (3, "Request Listing Agent Approval, Based On Our Working Relationship")), null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="bid_registration_status", on_delete=models.CASCADE, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    deposit_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)
    deposit_payment_success = models.BooleanField(default=0)
    session_id = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "bid_registration"


class ProofFunds(models.Model):
    registration = models.ForeignKey(BidRegistration, related_name="proof_funds_registration", on_delete=models.CASCADE, null=True, blank=True)
    upload = models.ForeignKey(UserUploads, related_name="proof_funds_upload", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="registration_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "proof_funds"


class BidLimit(Default):
    registration = models.ForeignKey(BidRegistration, related_name="bid_limit_registration", on_delete=models.CASCADE, null=True, blank=True)
    approval_limit = models.BigIntegerField(null=True, blank=True)
    is_approved = models.IntegerField(choices=((1, "Pending"), (2, "Approved"), (3, "Declined"), (4, "Not Interested")), default=1)
    status = models.ForeignKey(LookupStatus, related_name="bid_limit_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "bid_limit"


class BidRegistrationAddress(Default):
    registration = models.ForeignKey(BidRegistration, related_name="bid_registration_address_registration", on_delete=models.CASCADE, null=True, blank=True)
    address_type = models.IntegerField(choices=((1, "Agent"), (2, "Buyer"), (3, "Buyer/Agent")), default=1)
    email = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    address_first = models.CharField(max_length=255, null=True, blank=True)
    address_second = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="bid_registration_address_state", on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="bid_registration_address_country", on_delete=models.CASCADE, null=True, blank=True)
    mobile_no = models.CharField(max_length=12, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    auction = models.ForeignKey(PropertyAuction, related_name="bid_registration_address_auction", on_delete=models.CASCADE, null=True, blank=True)
    county = models.ForeignKey(LookupStateCounty, related_name="bid_registration_address_county", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="bid_registration_address_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "bid_registration_address"


class ViewBidRegistrationAddress(models.Model):
    """Database View for bid registration address
    """
    registration = models.ForeignKey(BidRegistration, on_delete=models.DO_NOTHING, related_name="view_bid_registration_address_registration")
    email = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    address_first = models.CharField(max_length=255, null=True, blank=True)
    address_second = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="view_bid_registration_address_state", on_delete=models.CASCADE, null=True, blank=True)
    mobile_no = models.CharField(max_length=12, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'view_bid_registration_address'


class BidMaxAmount(models.Model):
    """Bid Max Amount Model

    """
    user = models.ForeignKey(Users, related_name='bid_max_profile', on_delete=models.CASCADE)
    auction = models.ForeignKey(PropertyAuction, related_name='bid_max_auction', on_delete=models.CASCADE)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bid_max_amount'


class Bid(models.Model):
    """Model to save Bid.

    """
    domain = models.ForeignKey(NetworkDomain, related_name="bid_domain", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="bid_property", on_delete=models.CASCADE)
    registration = models.ForeignKey(BidRegistration, related_name="bid_registration_bid", on_delete=models.CASCADE, null=True, blank=True)
    auction = models.ForeignKey(PropertyAuction, related_name="bid_auction", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name='bid_user', on_delete=models.CASCADE)
    bid_date = models.DateTimeField(auto_now=True)
    bid_amount = models.DecimalField(max_digits=15, decimal_places=2, )
    highest_bid = models.BooleanField(default=0)
    user_qualify = models.BooleanField(default=0)
    is_canceled = models.BooleanField(default=0)
    bid_type = models.CharField(max_length=1, choices=(('1', 'Audit Only'), ('2', "Max Bid"), ('3', "Automatic")), null=True, default='1', blank=True)
    auction_type = models.IntegerField(choices=((1, 'Classic online'), (2, "Insider auction")), default=1, null=True, blank=True)
    insider_auction_step = models.IntegerField(choices=((1, 'Dutch'), (2, "Sealed bid"), (3, "English Action")), null=True, blank=True)
    ip_address = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'bid'


class BidCountView(models.Model):
    """Database View for bid count
    """
    property = models.ForeignKey(PropertyListing, related_name="bid_count_view_property", on_delete=models.DO_NOTHING)
    total = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'bid_count_view'


class ViewAuctionTimeLeft(models.Model):
    """Database View for auction time left
    """
    domain = models.ForeignKey(NetworkDomain, related_name="view_auction_time_left_domain", on_delete=models.DO_NOTHING)
    auction = models.ForeignKey(PropertyAuction, related_name="view_auction_time_left_auction", on_delete=models.DO_NOTHING)
    property = models.ForeignKey(PropertyListing, related_name="view_auction_time_left_property", on_delete=models.DO_NOTHING)
    time_left = models.IntegerField(null=True, blank=True)
    reserve_amount = models.FloatField(null=True, blank=True)
    max_bid = models.IntegerField(null=True, blank=True)
    winner = models.ForeignKey(Users, related_name="view_auction_time_left_winner", on_delete=models.DO_NOTHING)
    auction_type = models.ForeignKey(LookupAuctionType, related_name="view_auction_time_left_auction_type", on_delete=models.DO_NOTHING, db_column="auction_type")

    class Meta:
        managed = False
        db_table = 'view_auction_time_left'


class ViewBidHistory(models.Model):
    """Database View for bid history
    """
    # bidder_rand_name = models.ForeignKey(BidRegistration, related_name="view_bid_history_bidder_rand_name", on_delete=models.DO_NOTHING)
    bid_date = models.DateTimeField(null=True, blank=True)
    bid_amount = models.IntegerField(null=True, blank=True)
    bid_type = models.IntegerField(null=True, blank=True)
    property = models.ForeignKey(PropertyListing, related_name="view_bid_history_property", on_delete=models.DO_NOTHING)
    auction = models.ForeignKey(PropertyAuction, related_name="view_bid_history_auction", on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'view_bid_history'


class ViewMaxBidAmount(models.Model):
    """Database View for max bid amount
    """
    auction = models.ForeignKey(PropertyAuction, related_name="view_max_bid_amount_auction", on_delete=models.DO_NOTHING)
    max = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'view_max_bid_amount'


class MasterOffer(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="master_offer_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="master_offer_property", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="master_offer_user", on_delete=models.CASCADE)
    accepted_by = models.ForeignKey(Users, related_name="master_offer_accepted_by", on_delete=models.CASCADE, db_column="accepted_by", null=True, blank=True)
    accepted_amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)
    accepted_date = models.DateTimeField(null=True, blank=True)
    is_canceled = models.BooleanField(default=0)
    canceled_by = models.ForeignKey(Users, related_name="master_offer_canceled_by", on_delete=models.CASCADE, db_column="canceled_by", null=True, blank=True)
    cancel_reason = models.TextField(null=True, blank=True)
    is_declined = models.BooleanField(default=0)
    declined_by = models.ForeignKey(Users, related_name="master_offer_declined_by", on_delete=models.CASCADE, db_column="declined_by", null=True, blank=True)
    final_by = models.IntegerField(choices=((1, "Buyer"), (2, "Seller")), null=True, blank=True)
    declined_reason = models.TextField(null=True, blank=True)
    user_type = models.IntegerField(choices=((2, "Buyer"), (4, "Real Estate Agent")), default=2)
    working_with_agent = models.BooleanField(default=0, null=True, blank=True)
    property_in_person = models.IntegerField(choices=((1, "Yes, I have"), (2, "No, not yet"), (3, "I would like to see it")), default=1)
    pre_qualified_lender = models.IntegerField(choices=((1, "Yes, I have"), (2, "No, not yet"), (3, "I'm buying with all cash")), default=1)
    document = models.ForeignKey(UserUploads, related_name="master_offer_document", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="master_offer_status", on_delete=models.CASCADE)
    terms = models.BooleanField(default=1)
    steps = models.IntegerField(null=True, blank=True)
    document_comment = models.TextField(null=True, blank=True)
    behalf_of_buyer = models.BooleanField(default=0, null=True, blank=True)

    class Meta:
        db_table = "master_offer"


class OfferDocuments(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="offer_documents_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="offer_documents_property", on_delete=models.CASCADE)
    master_offer = models.ForeignKey(MasterOffer, related_name="offer_documents_master_offer", on_delete=models.CASCADE)
    document = models.ForeignKey(UserUploads, related_name="offer_documents_document", on_delete=models.CASCADE, null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="offer_documents_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "offer_documents"


class NegotiatedOffers(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="negotiated_offers_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="negotiated_offers_property", on_delete=models.CASCADE)
    master_offer = models.ForeignKey(MasterOffer, related_name="negotiated_offers_master_offer", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="negotiated_offers_user", on_delete=models.CASCADE)
    offer_by = models.IntegerField(choices=((1, "Buyer"), (2, "Seller")), default=1)
    display_status = models.IntegerField(choices=((1, "Make Offer"), (2, "Counter Offer"), (3, "Current Highest Offer")), default=1)
    offer_price = models.DecimalField(default=0.00, max_digits=17, decimal_places=2)
    comments = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="negotiated_offers_status", on_delete=models.CASCADE)
    best_offer_is_accept = models.BooleanField(default=0)
    best_offer_accept_by = models.ForeignKey(Users, related_name="negotiated_offers_accept_by", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "negotiated_offers"


class HighestBestNegotiatedOffers(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="highest_best_negotiated_offers_domain", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="highest_best_negotiated_offers_property", on_delete=models.CASCADE)
    master_offer = models.ForeignKey(MasterOffer, related_name="highest_best_negotiated_offers_master_offer", on_delete=models.CASCADE)
    user = models.ForeignKey(Users, related_name="highest_best_negotiated_offers_user", on_delete=models.CASCADE)
    offer_by = models.IntegerField(choices=((1, "Buyer"), (2, "Seller")), default=1)
    display_status = models.IntegerField(choices=((1, "Make Offer"), (2, "Counter Offer"), (3, "Current Highest Offer"), (4, "Offer Declined")), default=1)
    offer_price = models.DecimalField(default=0.00, max_digits=17, decimal_places=2)
    comments = models.TextField(null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="highest_best_negotiated_offers_status", on_delete=models.CASCADE)
    best_offer_is_accept = models.BooleanField(default=0)
    best_offer_accept_by = models.ForeignKey(Users, related_name="highest_best_negotiated_offers_accept_by", on_delete=models.CASCADE, null=True, blank=True)
    financing = models.IntegerField(choices=((1, "No Loan"), (2, "Conventional Loan"), (3, "VA Loan"), (4, "FHA Loan"), (5, "SBA  Loan"), (6, "1031 Exchange"), (7, "Other"), (8, " USDA/FSA Loan"), (9, "Bridge Loan"), (10, "Jumbo Loan"), (11, "Conduit/CMBS Loan")), default=1, null=True, blank=True)
    down_payment = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    earnest_money_deposit = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    due_diligence_period = models.IntegerField(choices=((1, "Yes, complete inspections at buyer(s) expense."), (2, "No, waive inspections."), (3, "16+ Days"),(4, "Waive Inspection")), default=1, null=True, blank=True)
    offer_contingent = models.IntegerField(choices=((1, "Yes"), (2, "No"), (3, "Cash Buyer")), default=1, null=True, blank=True)
    sale_contingency = models.BooleanField(default=1, null=True, blank=True)
    appraisal_contingent = models.BooleanField(default=1, null=True, blank=True)
    closing_period = models.IntegerField(choices=((1, "1-30 Days"), (2, "30-45 Days"), (3, "45-60 Days "), (4, "61+ Days")), default=1, null=True, blank=True)
    closing_cost = models.IntegerField(null=True, blank=True)
    declined_reason = models.TextField(null=True, blank=True)
    is_declined = models.BooleanField(default=0)

    class Meta:
        db_table = "highest_best_negotiated_offers"


class OfferAddress(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="offer_address_domain", on_delete=models.CASCADE)
    master_offer = models.ForeignKey(MasterOffer, related_name="offer_address_master_offer", on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    address_first = models.CharField(max_length=255, null=True, blank=True)
    address_second = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.ForeignKey(LookupState, related_name="offer_address_state", on_delete=models.CASCADE, null=True, blank=True)
    country = models.ForeignKey(LookupCountry, related_name="offer_address_country", on_delete=models.CASCADE, null=True, blank=True)
    mobile_no = models.CharField(max_length=12, null=True, blank=True)
    phone_no = models.CharField(max_length=12, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="offer_address_user", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="offer_address_status", on_delete=models.CASCADE)
    buyer_first_name = models.CharField(max_length=50, null=True, blank=True)
    buyer_last_name = models.CharField(max_length=50, null=True, blank=True)
    buyer_email = models.EmailField(max_length=254, null=True, blank=True)
    buyer_company = models.CharField(max_length=254, null=True, blank=True)
    buyer_phone_no = models.CharField(max_length=12, null=True, blank=True)

    class Meta:
        db_table = "offer_address"


class OfferDetail(Default):
    domain = models.ForeignKey(NetworkDomain, related_name="offer_detail_domain", on_delete=models.CASCADE)
    master_offer = models.ForeignKey(MasterOffer, related_name="offer_detail_master_offer", on_delete=models.CASCADE)
    earnest_money_deposit = models.DecimalField(max_digits=17, decimal_places=2)
    down_payment = models.DecimalField(max_digits=17, decimal_places=2, null=True, blank=True)
    due_diligence_period = models.IntegerField(choices=((1, "Yes, complete inspections at buyer(s) expense."), (2, "No, waive inspections."), (3, "16+ Days"), (4, "Waive Inspection")), default=1)
    closing_period = models.IntegerField(choices=((1, "1-30 Days"), (2, "30-45 Days"), (3, "45-60 Days "), (4, "61+ Days")), default=1)
    financing = models.IntegerField(choices=((1, "No Loan"), (2, "Conventional Loan"), (3, "VA Loan"), (4, "HUD/FHA Loan"), (5, "SBA  Loan"), (6, "1031 Exchange"), (7, "Other"), (8, "USDA Loan")), default=1)
    offer_contingent = models.IntegerField(choices=((1, "Yes"), (2, "No"), (3, "Cash Buyer")), default=1)
    sale_contingency = models.BooleanField(default=1)
    appraisal_contingent = models.BooleanField(default=1)
    closing_cost = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(Users, related_name="offer_detail_user", on_delete=models.CASCADE)
    status = models.ForeignKey(LookupStatus, related_name="offer_detail_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "offer_detail"


class InsiderAuctionStepWinner(Default):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    domain = models.ForeignKey(NetworkDomain, related_name="insider_auction_step_winner_domain", on_delete=models.CASCADE)
    bid = models.ForeignKey(Bid, related_name="insider_auction_step_winner_bid", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, related_name="insider_auction_step_winner_user", on_delete=models.CASCADE)
    property = models.ForeignKey(PropertyListing, related_name="insider_auction_step_winner_property", on_delete=models.CASCADE)
    auction = models.ForeignKey(PropertyAuction, related_name="insider_auction_step_winner_auction", on_delete=models.CASCADE)
    insider_auction_step = models.IntegerField(choices=((1, 'Dutch'), (2, "Sealed bid"), (3, "English Action")), null=True, blank=True)
    status = models.ForeignKey(LookupStatus, related_name="insider_auction_step_winner_status", on_delete=models.CASCADE)

    class Meta:
        db_table = "insider_auction_step_winner"





