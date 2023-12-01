from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from core.models import User


class MyOIDCAB(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        return user

    def update_user(self, user, claims):
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

    def verify_claims(self, claims):
        verified = super(MyOIDCAB, self).verify_claims(claims)
        return verified
