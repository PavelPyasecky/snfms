from copy import deepcopy

from django.conf import settings
from querybuilder import query, fields, tables


class CountField(fields.CountField):

    def get_field_identifier(self):
        return '*'


class DateAddField(fields.SimpleField):

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, offset=settings.SF_TIME_OFFSET):
        self.offset = offset
        super(DateAddField, self).__init__(field, table, alias, cast, distinct)

    def get_select_sql(self):
        return 'DATEADD(hour, {1}, {0}) '.format(self.field, -self.offset)


class Limit(query.Limit):

    def __init__(self, query, limit=None, offset=None):
        self.query = query
        super(Limit, self).__init__(limit, offset)

    def get_sql(self):
        sql = ''
        if not self.query.sorters:
            sql += 'ORDER BY 1 '

        sql += 'OFFSET {0} ROWS '.format(self.offset)

        if self.limit > 0:
            sql += 'FETCH NEXT {0} ROWS ONLY '.format(self.limit)

        return sql


class Query(object):
    methods = (
        'query_field',
        'query_field_name',
        'apply_joins',
        'limit',
        'copy',
        'count',
        'delete_connection',
        'set_connection',
    )

    def __new__(cls, *args, **kwargs):
        """
        This deep magic is needed because internal querybuilder logic expects that
        query is exactly the instance of the querybuilder.query.Query class
        """
        instance = query.Query(*args, **kwargs)

        for method in cls.methods:
            setattr(instance, method, getattr(cls, method).__get__(instance, instance.__class__))

        return instance

    def query_field_name(self, field, prefix):
        if prefix:
            return '%s.%s' % (prefix, field.name)

        return field.name

    def query_field(self, field_alias):
        """
        Looks for a field by alias in all the tables.
        We need it for filtering and ordering
        """
        for table in self.tables:
            field = table.find_field(alias=field_alias)
            if field:
                return self.query_field_name(field, table.get_field_prefix())

        for join in self.joins:
            field = join.right_table.find_field(alias=field_alias)
            if field:
                return self.query_field_name(field, join.right_table.get_field_prefix())

    def apply_joins(self, joins):
        for join in joins:
            self.join(*join)

        return self

    def limit(self, limit=0, offset=0):
        """
        Original limit doesn't work with the sqlserver backend
        """
        self._limit = Limit(self, limit, offset)

    def delete_connection(self, query):
        connection = query.connection
        del query.connection

        for table in query.tables:
            if isinstance(table, tables.QueryTable):
                self.delete_connection(table.query)

        return connection

    def set_connection(self, query, connection):
        query.connection = connection

        for table in query.tables:
            if isinstance(table, tables.QueryTable):
                self.set_connection(table.query, connection)

    def copy(self):
        """
        Original copy fails if query.table is instance of QueryTable
        We need to delete and set connection attribute recursively
        """
        connection = self.delete_connection(self)
        copied_query = deepcopy(self)

        self.set_connection(self, connection)
        self.set_connection(copied_query, connection)

        return copied_query

    def count(self):
        """
        Original count doesn't work with the sqlserver backend
        """
        copied_query = self.copy()

        copied_query.sorters = []
        count_query = query.Query(self.connection).from_table(copied_query, [CountField('*', alias='count')])

        return count_query.select()[0]['count']
