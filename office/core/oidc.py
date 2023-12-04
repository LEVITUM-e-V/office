from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.conf import settings
from core.models import User
from josepy.b64 import b64decode
import requests
import json


class MyOIDCAB(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)

        groups = claims.get('groups', [])

        if settings.OIDC_ADMIN_GROUP in groups:
            user.is_staff = True
            user.is_superuser = True

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        return user

    def update_user(self, user, claims):
        groups = claims.get('groups', [])
        if settings.OIDC_ADMIN_GROUP in groups:
            user.is_staff = True
            user.is_superuser = True
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        return user

    def filter_users_by_claims(self, claims):
        email = claims.get('email')
        if not email:
            return self.UserModel.objects.none()

        try:
            user = User.objects.get(email=email)
            return [user]

        except User.DoesNotExist:
            return self.UserModel.objects.none()

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details dictionary. The id_token and payload are not used in
        the default implementation, but may be used when overriding this method"""

        user_response = requests.get(
            self.OIDC_OP_USER_ENDPOINT,
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        _, payload_data, _ = id_token.split(".")
        payload_data = b64decode(payload_data)
        payload_data = json.loads(payload_data.decode('utf-8'))
        groups = payload_data.get('groups', [])
        user_response.raise_for_status()
        return {
                'groups': groups,
                **user_response.json()
                }

    def verify_claims(self, claims):
        verified = super(MyOIDCAB, self).verify_claims(claims)
        groups = claims.get('groups', [])

        if settings.OIDC_USER_GROUP not in groups:
            return False
        return verified
