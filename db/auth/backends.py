import base64
import binascii
import re
from hashlib import sha256
from Crypto.Cipher import AES

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import make_password
from django.db import transaction

from db.controller.models import Customer
from db.customer.models import User


def parse_user_name_and_domain_from_email_address(username: str) -> (str, str):
    if '@' not in username:
        raise UsernameNeedsAtSymbol
    return username.rsplit('@', 1)


def decode_phrase(encoded_phrase: str) -> bytes:
    try:
        return base64.b64decode(encoded_phrase)
    except binascii.Error:
        raise UnacceptablePassphrase


def encode_phrase(phrase: str) -> bytes:
    return phrase.encode()


def create_hash(phrase: str) -> bytes:
    return sha256(phrase.encode()).digest()


def decrypt_password(password):
    # TODO: Use sfdb.auth.utils.AESCrypt
    #       Don't use static iv...
    c = AES.new(settings.AES_PASSCODE, AES.MODE_CBC, settings.AES_IV)
    try:
        password = c.decrypt(base64.standard_b64decode(str(password))).decode('utf-8')
    except (binascii.Error, ValueError):
        raise UnacceptablePassphrase

    return re.sub('[\x00-\x16]', '', password)  # This is not good.


class UnacceptablePassphrase(Exception):
    pass


class NoSuchCustomer(Exception):
    pass


class NoSuchUser(Exception):
    pass


class UsernameNeedsAtSymbol(Exception):
    pass


class UserNeedsEmailAddress(Exception):
    pass


class SalesFusionBackend(ModelBackend):
    # username = internet auth email address -- user_name and domain
    # user_name = internal user record unique username

    def authenticate(self, request, username=None, password=None, **kwargs):
        already_authenticated_user = self._user_is_already_authenticated(request, username, password, **kwargs)

        if already_authenticated_user:
            return already_authenticated_user
        else:
            try:
                return self._authenticate_new_user(username, password)
            except (UserNeedsEmailAddress, UsernameNeedsAtSymbol, NoSuchCustomer, NoSuchUser, UnacceptablePassphrase):
                return

    def _user_is_already_authenticated(self, request, username, password, **kwargs):
        return super(SalesFusionBackend, self).authenticate(request, username, password, **kwargs)

    def _authenticate_new_user(self, username: str, password: str):
        user_name, domain = parse_user_name_and_domain_from_email_address(username)
        self._get_customer(domain)
        passphrase = self._prepare_passphrase(password)
        customer_user = self._get_customer_user(user_name, domain)
        shibboleth = self._get_authority(customer_user)

        if passphrase != shibboleth:
            raise UnacceptablePassphrase

        return self._update_or_create_local_user(username, customer_user, password)

    def _get_customer(self, domain):
        try:
            return Customer.objects.using('controller').filter(domain_name=domain, process_active=1, login=1)
        except (Customer.MultipleObjectsReturned, Customer.DoesNotExist):
            raise NoSuchCustomer

    def _prepare_passphrase(self, original_password: str) -> bytes:
        raise NotImplementedError

    def _get_customer_user(self, user_name: str, domain: str) -> User:
        try:
            return User.objects.using(domain).only(
                'hashed_key',
                'user_name',
                'first_name',
                'last_name',
                'email'
            ).get(user_name=user_name)
        except (User.MultipleObjectsReturned, User.DoesNotExist):
            raise NoSuchUser

    def _get_authority(self, source):
        return source.hashed_key

    def _update_or_create_local_user(self, username: str, customer_user: User, password: str):
        model = get_user_model()

        if customer_user.email is None:
            raise UserNeedsEmailAddress

        with transaction.atomic():
            user, _ = model.objects.update_or_create(
                defaults={
                    'email': model.objects.normalize_email(customer_user.email),
                    'password': make_password(password),
                    'first_name': customer_user.first_name or '',
                    'last_name': customer_user.last_name or '',
                },
                username=username,
            )

        return user

    def get_user(self, user_id):
        model = get_user_model()

        try:
            return model.objects.get(pk=user_id)
        except model.DoesNotExist:
            return


class Frodo(SalesFusionBackend):

    def _prepare_passphrase(self, original_password: str) -> bytes:
        return create_hash(original_password)


class Gandalf(SalesFusionBackend):

    def _prepare_passphrase(self, original_password: str) -> bytes:
        decrypted_password = decrypt_password(original_password)
        return create_hash(decrypted_password)


class Saruman(SalesFusionBackend):

    def _prepare_passphrase(self, original_password: str) -> bytes:
        return decode_phrase(decrypt_password(original_password))
