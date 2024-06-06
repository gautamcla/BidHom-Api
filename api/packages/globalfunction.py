import base64
from random import randint
import re
from api.users.models import *
import uuid
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


def b64encode(source):
    source = "xsd0xa" + source + "xsd1xa"
    source = source.encode('utf-8')
    content = base64.b64encode(source).decode('utf-8')
    return content


def b64decode(source):
    content = base64.b64decode(source).decode('utf-8')
    content = content[6::]
    content = content[:-6:]
    return content


def random_with_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)


def remove_space(string):
    string = string.lower().strip()
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', string)


def remove_special(string):
    # return re.sub("[!@#$%^&*-_(){}/|=?':.]", "", string)
    return re.sub("[^A-Za-z]", "", string)


def make_subdomain(string):
    string = remove_space(string)
    string = remove_special(string)
    network_domain = NetworkDomain.objects.filter(domain_name=string).first()
    if network_domain is None:
        return string
    else:
        random_digit = random_with_digits(4)
        domain_name = string + str(random_digit)
        return domain_name


def forgot_token():
    try:
        u_id = uuid.uuid4()
        return u_id.time_low
    except Exception as exp:
        return False


def replace_space(string):
    string = string.lower().strip()
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '_', string)


def get_cache(cache_name):
    try:
        if settings.REDIS_CACHE == "True" and cache_name in cache and cache.get(cache_name) != "" and len(list(cache.get(cache_name))) > 0:
            all_data = list(cache.get(cache_name))
        else:
            all_data = None
        return all_data
    except Exception as exp:
        return None


def set_cache(cache_name, data):
    try:
        if settings.REDIS_CACHE == "True":
            cache.set(cache_name, data, timeout=int(CACHE_TTL))
        return True
    except Exception as exp:
        return False


def unique_registration_id():
    try:
        u_id = uuid.uuid4()
        return u_id.time_low
    except Exception as exp:
        return False

