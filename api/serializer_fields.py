import json
from datetime import timedelta, datetime
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import Field, DateTimeField
from snfms.settings import TIME_OFFSET


class SemicolonDelimitedListField(Field):

    def to_representation(self, obj):
        return obj.split(';') if len(obj) > 0 else []

    def to_internal_value(self, data):
        return ';'.join(data)


class OffsetDateTimeField(DateTimeField):

    def to_internal_value(self, value):
        value = value + timedelta(hours=SF_TIME_OFFSET)
        return super(OffsetDateTimeField, self).to_internal_value(value)

    def to_representation(self, value):
        # this check is only for the unit tests
        if value and isinstance(value, datetime):
            value = value - timedelta(hours=SF_TIME_OFFSET)
            return super(OffsetDateTimeField, self).to_representation(value)

        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S") - timedelta(hours=SF_TIME_OFFSET)
            return super(OffsetDateTimeField, self).to_representation(value)
        except ValueError:
            return


class OptionsMappingField(Field):

    # The options argument should be a tuple of tuples defined on the model
    # See Campaign.EDITOR_TYPE_CHOICES for an example
    def __init__(self, options, **kwargs):
        self.options = dict(options)
        self.reversed_options = dict((value, key) for key, value in options)

        super(OptionsMappingField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self.options.get(obj)

    def to_internal_value(self, data):
        return self.reversed_options.get(data)


class CaseInsensitiveOptionsMappingField(Field):

    # This version handles cases where existing values in the database do not
    # follow consistent casing. Always returns proper casing.
    def __init__(self, options, **kwargs):
        self.options = dict((key.lower(), value) for key, value in options)
        self.reversed_options = dict((value, key) for key, value in options)

        super(CaseInsensitiveOptionsMappingField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return self.options.get(obj.lower())

    def to_internal_value(self, data):
        return self.reversed_options.get(data)


class IntegerHyperLinkedRelatedField(HyperlinkedRelatedField):
    """
    This field is for db columns that are integer fields with no fk constraint.
    If db column allows negative integers the normal HyperlinkedRelatedField
    will cause this error: django.core.urlresolvers.NoReverseMatch
    """

    def get_url(self, obj, view_name, request, format):

        lookup_value = getattr(obj, self.lookup_field)
        if isinstance(lookup_value, int) and lookup_value < 1:
            return None

        return super(IntegerHyperLinkedRelatedField, self).get_url(obj, view_name, request, format)


class JsonField(Field):

    def to_representation(self, obj):
        if obj is None or obj == '':
            return obj
        return json.loads(obj)

    def to_internal_value(self, data):
        return json.dumps(data)
