from api.users.models import *
from oauth2_provider.models import AccessToken, Application, Grant, RefreshToken
import hashlib
import time
import requests
from django.conf import settings


def create_application(user_id):
    """
    Create OAuth2 Application for users
    :param user_id:
    :return: True/False
    """
    try:
        users = Users.objects.get(id=user_id)
        ts = time.time()
        client_secret = hashlib.sha512(str(str(users.email) + str(ts)).encode('utf-8')).hexdigest()
        client_id = client_secret[-50::]
        application = Application()
        application.user_id = user_id
        application.client_id = client_id
        application.client_type = "confidential"
        application.authorization_grant_type = "password"
        application.client_secret = client_secret
        application.name = str(users.first_name)+" Application"
        application.save()
        return True
    except Exception as exp:
        return False


def oauth_token(user_id, password):
    """
    Get OAuth2 Token for users
    :param user_id:
    :param password:
    :return:
    """
    try:
        users = Users.objects.get(id=user_id)
        oauth_application = Application.objects.get(user_id=users.id)
        token_url = settings.BASE_URL+"/o/token/"
        r = requests.post(
            token_url,
            data={
                'grant_type': 'password',
                'username': users.email,
                'password': password,
                'client_id': oauth_application.client_id,
                'client_secret': oauth_application.client_secret,
            },
        )
        token = r.json()
        return token
    except Exception as exp:
        return False


def refresh_token(user_id, refresh):
    """
    Get Refresh Token
    :param user_id:
    :param refresh:
    :return:
    """
    try:
        oauth_application = Application.objects.get(user_id=user_id)
        token_url = settings.BASE_URL + "/o/token/"
        r = requests.post(
            token_url,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh,
                'client_id': oauth_application.client_id,
                'client_secret': oauth_application.client_secret,
            },
        )
        return r.json()
    except Exception as exp:
        return False


def revoke_token(user_id, token):
    try:
        oauth_application = Application.objects.get(user_id=user_id)
        token_url = settings.BASE_URL + "/o/revoke_token/"
        r = requests.post(
            token_url,
            data={
                'token': token,
                'client_id': oauth_application.client_id,
                'client_secret': oauth_application.client_secret,
            },
        )
        if r.status_code == requests.codes.ok:
            # return Response({'message': 'token revoked'}, r.status_code)
            return True
        # Return the error if it goes badly
        # return Response(r.json(), r.status_code)
        return False
    except Exception as exp:
        return False


def user_details(token):
    try:
        access = AccessToken.objects.get(token=token)
        return access.user_id
    except Exception as exp:
        return False