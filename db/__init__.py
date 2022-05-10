import threading

from django.conf import settings

request_cfg = threading.local()


def get_user_info_from_user(user):
    if '@' not in user.username:
        return user.username, None
    try:
        (sf_username, domain) = user.username.rsplit('@', 1)
    except:
        return user.username, None
    return sf_username, domain


def get_customer_id_from_header(request):
    return request.META.get("HTTP_X_CUSTOMER_ID")


def get_user_info_from_request(request):
    user = request.user
    return get_user_info_from_user(user)


def get_customer_domain_from_user(user):
    (sf_username, domain) = get_user_info_from_user(user)

    return domain, sf_username


def get_customer_domain_from_request(request):
    (sf_username, domain) = get_user_info_from_request(request)

    return domain


class MasterRouter (object):
    def _default_db(self, model):
        if model._meta.app_label in ['contenttypes', 'sessions', 'sites', 'auth']:
            return None
        if model._meta.app_label == 'sfdb' and hasattr(request_cfg, 'customer_domain_name'):
                return request_cfg.customer_domain_name
        return 'default'

    def db_for_read(self, model, **hints):
        if model._meta.app_label in ['contenttypes', 'sessions', 'sites', 'auth']:
            return None
        db = getattr(getattr(hints.get("instance", None), "_state", None), "db", None)
        if db:
            return db
        return self._default_db(model)

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ['contenttypes', 'sessions', 'sites', 'auth']:
            return None
        db = getattr(getattr(hints.get("instance", None), "_state", None), "db", None)
        if db:
            return db
        return self._default_db(model)

    def allow_relation(self, obj1, obj2):
        return True

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label in ['contenttypes', 'sessions', 'sites', 'auth', 'db']:
            return db == 'default'
        return None


class ControllerRouter (object):
    ROUTE_MODEL_NAMES = settings.CONTROLLER_MODEL_NAMES
    DB_NAME = 'controller'

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.ROUTE_MODEL_NAMES:
            return self.DB_NAME
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.ROUTE_MODEL_NAMES:
            return self.DB_NAME
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in ['db', ]:
            return db == 'controller'
        return None
