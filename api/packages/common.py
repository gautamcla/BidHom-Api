from api.notifications.models import *


def add_notification(domain_id, title, content, user_id, added_by, notification_for, property_id="", notification_type=1):
    try:
        redirect_url = ""
        if notification_type == 1:
            redirect_url = "/asset-details/?property_id="+str(property_id)
        elif notification_type == 2:
            redirect_url = "/admin/listing/"
        elif notification_type == 3:
            redirect_url = "/admin/"
        elif notification_type == 4:
            redirect_url = "/admin/listing/?auction_type=traditional offer"
        elif notification_type == 5:
            redirect_url = "/edit-profile/"
        elif notification_type == 6:
            redirect_url = "/admin/listing/?auction_type=highest offer"
        elif notification_type == 7:
            redirect_url = "/admin/listing/?auction_type=live offer"
        elif notification_type == 8:
            redirect_url = "/admin/listing/?auction_type=insider auction"
        event_notification = EventNotification()
        event_notification.domain_id = domain_id
        event_notification.notification_for = notification_for
        event_notification.title = title
        event_notification.content = content
        event_notification.user_id = user_id
        event_notification.added_by_id = added_by
        event_notification.status_id = 1
        event_notification.redirect_url = redirect_url
        event_notification.save()
        return True
    except Exception as exp:
        return False


def number_format(number):
    try:
        number = "{:,}".format(int(number))
        return number
    except Exception as exp:
        return 0


def phone_format(phone):
    try:
        number = str(phone)
        first = number[0:3]
        second = number[3:6]
        third = number[6:10]
        phone_no = '(' + first + ')' + ' ' + second + '-' + third
        return phone_no
    except Exception as exp:
        return 0


def int_to_en(num):
    d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven', 8: 'eight', 9: 'nine',
         10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen', 15: 'fifteen', 16: 'sixteen',
         17: 'seventeen', 18: 'eighteen', 19: 'nineteen', 20: 'twenty', 30: 'thirty', 40: 'forty', 50: 'fifty',
         60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninety'}
    k = 1000
    m = k * 1000
    b = m * 1000
    t = b * 1000

    assert(0 <= num)
    if num < 20:
        return d[num]

    if num < 100:
        if num % 10 == 0:
            return d[num]
        else:
            return d[num // 10 * 10] + ' ' + d[num % 10]

    if num < k:
        if num % 100 == 0:
            return d[num // 100] + ' hundred'
        else:
            return d[num // 100] + ' hundred ' + int_to_en(num % 100)

    if num < m:
        if num % k == 0:
            return int_to_en(num // k) + ' thousand'
        else:
            return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

    if num < b:
        if num % m == 0:
            return int_to_en(num // m) + ' million'
        else:
            return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

    if num < t:
        if num % b == 0:
            return int_to_en(num // b) + ' billion'
        else:
            return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

    if num % t == 0:
        return int_to_en(num // t) + ' trillion'
    else:
        return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)
    raise AssertionError('num is too large: %s' % str(num))