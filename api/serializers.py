import json
import codecs
from collections import OrderedDict
from copy import copy
from datetime import date
from typing import Union, Iterator, List, Mapping, NoReturn, Dict, Type

import django_excel
from rest_framework import serializers
from rest_framework.utils import model_meta

import tools
from api.decorators import stored_method
from api.utils import get_utc_now
from db import get_customer_domain_from_request, get_user_info_from_request


# Validate that an instance update is not a noop
from db.customer import models


def diff_validated_data(instance, validated_data, excludes=[], json_fields=[]):
    excludes.extend(json_fields)
    for attr, value in validated_data.items():
        if attr not in excludes and hasattr(instance, attr) and getattr(instance, attr) != value:
            return True

        # So, comparing json blobs... I found several options. There is a jsoncompare package
        # that is incompatible with Python3. There's an outstanding request for a patch, which
        # would be easy to facilitate, I went ahead and patched it for the hell of it, you can see it here:
        # https://github.com/wizzbiff/jsoncompare/tree/support-for-python3
        # Also, there was this simple solution on stack overflow:
        # http://stackoverflow.com/a/25851972
        # However, just comparing json objects seems to work for our purposes (for now). This is
        # contingent on the fact that we don't have lists in our json objects, because
        # the ordering of a list will be considered, which makes this potentially fragile
        if attr in json_fields and hasattr(instance, attr):
            json_a = json.loads(getattr(instance, attr))
            json_b = json.loads(value)
            if json_a != json_b:
                return True

    return False


class AutoUpdateMixinBase(object):

    def get_auto_fields(self, action):
        return {}

    def create(self, validated_data):
        return super(AutoUpdateMixinBase, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self.update_fields('update', validated_data)
        return super(AutoUpdateMixinBase, self).update(instance, validated_data)

    def update_fields(self, action, validated_data):
        for fields, get_auto_value in self.get_auto_fields(action).items():
            value = getattr(self, get_auto_value)()
            validated_data.update(dict((field, value) for field in fields if field))

        return validated_data


class ListAutoUpdateMixin(AutoUpdateMixinBase):
    def update_fields(self, action, validated_data):
        for fields, get_auto_value in self.get_auto_fields(action).items():
            value = getattr(self, get_auto_value)()
            for item in validated_data:
                item.update(dict((field, value) for field in fields if field))
        return validated_data


class AutoNowMixin(AutoUpdateMixinBase):
    created_date_field = 'created_date'
    updated_date_field = 'updated_date'

    def get_auto_fields(self, action):
        auto_fields_map = {
            'create': {(self.created_date_field, self.updated_date_field): 'get_now'},
            'update': {(self.updated_date_field,): 'get_now'}
        }
        auto_fields = super(AutoNowMixin, self).get_auto_fields(action)
        auto_fields.update(auto_fields_map.get(action, {}))

        return auto_fields

    def get_now(self):
        return get_utc_now()

    def get_today(self):
        return date.today()


class UserMixin:
    @stored_method
    def get_user(self):
        username, domain = get_user_info_from_request(self.context['request'])
        return models.User.objects.using(domain).get(user_name=username)

    def get_user_pk(self):
        return self.get_user().pk

    def get_user_domain(self):
        return get_customer_domain_from_request(self.context['request'])


class AutoUserMixin(UserMixin, AutoUpdateMixinBase):
    created_by_field = 'created_by_id'
    updated_by_field = 'updated_by_id'

    def get_auto_fields(self, action):
        auto_fields = super(AutoUserMixin, self).get_auto_fields(action)

        auto_fields_map = {
            'create': {(self.created_by_field, self.updated_by_field): 'get_user_pk'},
            'update': {(self.updated_by_field,): 'get_user_pk'}
        }

        auto_fields.update(auto_fields_map.get(action, {}))

        return auto_fields


class ModelManagerSerializer(serializers.ModelSerializer):

    """
    The only difference of this 'create' from the original one is using
    of the self.Meta.model_manager for creation of new instances.
    It allows to use different model managers for the same endpoint
    """

    @property
    def model_manager(self):
        if hasattr(self.Meta, 'model_manager'):
            return self.Meta.model_manager

        return self.Meta.model.objects.using(get_customer_domain_from_request(self.context['request'])).all()

    def create(self, validated_data):
        serializers.raise_errors_on_nested_writes('create', self, validated_data)

        ModelClass = self.Meta.model

        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        try:
            instance = self.model_manager.create(**validated_data)
        except TypeError as exc:
            msg = (
                'Got a `TypeError` when calling `%s.objects.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception text was: %s.' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
                    self.__class__.__name__,
                    exc
                )
            )
            raise TypeError(msg)

        if many_to_many:
            for field_name, value in many_to_many.items():
                setattr(instance, field_name, value)

        return instance


class DateAggregationSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField()
    date = serializers.SerializerMethodField()

    def get_interval(self):
        return self.context['view'].get_interval()

    def get_date(self, obj):
        return obj[self.get_interval()].strftime('%Y-%m-%d')


class QuerySerializer(serializers.Serializer):

    def to_representation(self, instance):
        result = OrderedDict()
        fields = getattr(self.Meta, 'fields', instance.keys())

        for field in fields:
            result[field] = instance.get(field)

        return result

    class Meta:
        pass


class CustomFieldValidationMixin(object):

    def verify_custom_fields(self, instance, validated_data):
        if 'custom_fields' in validated_data:
            instance.sync_dynamic_fields()
            custom_fields = validated_data.pop('custom_fields', {})
            invalid_fields = instance._validate_dynamic_field_data(custom_fields)
            if invalid_fields:
                raise serializers.ValidationError(invalid_fields)

            validated_data.update(custom_fields)


class DeserializerBase(serializers.Serializer):
    serializer = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields = self.serializer._declared_fields.items()
        for field_name, field in fields:
            new_field = copy(field)
            new_field.source = field_name
            self.fields[field.source] = new_field


class MagicStringSerializer(serializers.Serializer):
    magic_string = serializers.CharField()


class ManageUISerializer(serializers.ModelSerializer):
    updated_date = serializers.DateTimeField(read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.name', read_only=True)
    updated_by_id = serializers.IntegerField(source='updated_by.user_id', read_only=True)

    created_date = serializers.DateTimeField(read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    created_by_id = serializers.IntegerField(source='created_by.user_id', read_only=True)


class ParentObjectRetrievalMixin:
    def get_parent_object(self, key, model):
        parent_id = self.context['view'].kwargs[key]
        customer_domain = get_customer_domain_from_request(self.context['request'])
        return model.objects.using(customer_domain).get(pk=parent_id)


SpreadsheetFile = Union[django_excel.ExcelInMemoryUploadedFile, django_excel.TemporaryUploadedExcelFile]


class SpreadsheetSerializer(serializers.ListSerializer):

    serializer: Type[serializers.Serializer] = None

    # A mapping of spreadsheet column names to their equivalent model field name used to rename columns prior to
    # model serialization/deserialization.
    remap_columns: Dict[str, str] = {}

    max_file_size = 5242880  # 5MB

    # When True and the row serializer is a subclass of ModelSerializer, the models will be created in bulk instead
    # of one at a time.  The model instances are created by passing data as kwargs to the model class instead of the
    # `create()` method of the serializer.  If your serializer overrides `create()` to set fields of the model you will
    # need to disable this flag or override the `record_to_internal_value()` method to set that data instead.
    bulk_create = True
    bulk_create_batch_size = 100

    def __init__(self, *args, **kwargs):
        child_kwargs = {}
        if 'context' in kwargs:
            child_kwargs['context'] = kwargs['context']
        kwargs['child'] = self.serializer(**child_kwargs)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, spreadsheet: SpreadsheetFile) -> List[Mapping]:
        records = []
        try:
            for record in self.iget_records(spreadsheet):
                for from_col, to_col in self.remap_columns.items():
                    try:
                        record[to_col] = record.pop(from_col)
                    except KeyError:
                        raise serializers.ValidationError(
                            'No column named "{col_name}" in spreadsheet'.format(col_name=from_col))
                self.record_to_internal_value(record)
                records.append(record)
        finally:
            spreadsheet.free_resources()
        return super().to_internal_value(records)

    def to_representation(self, data) -> NoReturn:
        raise NotImplementedError("Serialization to spreadsheet not implemented")

    def run_validation(self, data=serializers.empty):
        if isinstance(data, (django_excel.ExcelInMemoryUploadedFile, django_excel.TemporaryUploadedExcelFile)):
            if data.size > self.max_file_size:
                raise serializers.ValidationError(
                    f'spreadsheet file exceeds maximum size of {self.max_file_size} bytes')
        return super().run_validation(data=data)

    def create(self, validated_data):
        if not self.bulk_create:
            return super().create(validated_data)

        try:
            model_klass = self.serializer.Meta.model
        except AttributeError:
            return super().create(validated_data)

        return model_klass.objects.bulk_create([model_klass(**item) for item in validated_data],
                                               batch_size=self.bulk_create_batch_size)

    def iget_records(self, spreadsheet: SpreadsheetFile, **kwargs) -> Iterator[OrderedDict]:
        """Returns an iterator for the rows of a spreadsheet.

        This method determines what parameters are needed in the call to the iget_records() method of the given
        spreadsheet file.  Keyword args passed to this method will override any values passed to iget_records().  If
        there are additional parameters needed to handle your spreadsheet file you may override this method and call
        the superclass method with the desired values.
        """
        params = {
            'skip_empty_rows': True,
        }

        if spreadsheet.content_type.endswith('csv'):
            # Excel will include a byte order mark (BOM) at the beginning of csv files it creates when saving as
            # "CSV UTF-8".  The pyexcel library seems to have issues detecting this case and needs to explicitly be
            # passed the correct encoding otherwise it will include the BOM as part of the first cell's value.
            spreadsheet.seek(0)  # The BOM is found at the beginning of the file.
            bom = spreadsheet.read(len(codecs.BOM_UTF8))
            if bom == codecs.BOM_UTF8:
                params['encoding'] = 'utf-8-sig'

        params.update(kwargs)
        return spreadsheet.iget_records(**params)

    def record_to_internal_value(self, record: OrderedDict) -> None:
        """Handle initialization/modification of a spreadsheet row record for deserialization.

        Override this method to handle any changes necessary to deserialize a row to the target model.  Modify the
        record dict to add additional fields or convert values to their appropriate types.  If there are any issues
        with the record that would prevent successful deserialization a ValidationError should be raised.  Note that
        this method is called after columns have been remapped.
        """


class DynamoDBQueryResultsPageSerializer(serializers.Serializer):
    total_count = serializers.IntegerField(min_value=0, help_text='Total number of items to be retrieved')
    count = serializers.IntegerField(min_value=0, help_text='Number of items retrieved from the current request')
    page_size = serializers.IntegerField(min_value=1, help_text='Specified size of results pages')
    next_page_key = serializers.CharField(allow_null=True, help_text='Query param token for the next page of results, '
                                                                     'if there any')
    results = serializers.ListField(allow_empty=True, help_text='Query results data')


class ModelFieldsSerializer(serializers.Serializer):
    column_name = serializers.CharField(source='COLUMN_NAME')
    data_type = serializers.CharField(source='DATA_TYPE')
    max_length = serializers.SerializerMethodField()

    def get_max_length(self, instance):
        return instance['CHARACTER_MAXIMUM_LENGTH'] or 0


class BulkListSerializer(serializers.ListSerializer):
    child = NotImplementedError
    many = NotImplementedError

    bulk_create_batch_size = 100

    def create(self, validated_data):
        try:
            model_class = self.child.Meta.model
        except AttributeError:
            return super().create(validated_data)

        return model_class.objects.bulk_create([model_class(**item) for item in validated_data],
                                               batch_size=self.bulk_create_batch_size)


class UserManageUICreateSerializer(serializers.ModelSerializer):
    """
    This mixin is used for solving a problem with duplicated requests to
    database while showing user fields after instance creation
    Requires AutoUserMixin that is usually used separately
    """

    updated_by_name = serializers.SerializerMethodField()
    updated_by_id = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    created_by_id = serializers.SerializerMethodField()

    def get_updated_by_id(self, _):
        return self.get_user_pk()

    def get_created_by_id(self, _):
        return self.get_user_pk()

    def get_created_by_name(self, _):
        return self.get_user().name

    def get_updated_by_name(self, _):
        return self.get_user().name
