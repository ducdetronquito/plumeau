from collections import namedtuple
from contextlib import closing
import sqlite3

__all__ = [
    'Field', 'FloatField', 'ForeignKeyField', 'IntegerField',
    'Model', 'PrimaryKeyField', 'SQLiteDB', 'TextField',
]


class CSV(tuple):
    """Output a iterable as coma-separated value."""
    __slots__ = ()

    def __str__(self):
        return ', '.join(str(value) for value in self)


class BracketCSV(CSV):
    """Output a iterable as coma-separated value between brackets."""
    __slots__ = ()

    def __str__(self):
        return '(' + super().__str__() + ')'


class Transaction:
    __slots__ = ('connection')

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.execute('BEGIN')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.execute('ROLLBACK')
        else:
            self.connection.execute('COMMIT')


class SQLiteDB:
    __slots__ = ('db_name', '_connection')

    # Create table query
    AUTOINCREMENT = 'AUTOINCREMENT'
    CREATE = 'CREATE'
    DEFAULT = 'DEFAULT'
    EXISTS = 'EXISTS'
    IF = 'IF'
    INTEGER = 'INTEGER'
    NOT_NULL = 'NOT NULL'
    PK = 'PRIMARY KEY'
    REAL = 'REAL'
    REFERENCES = 'REFERENCES'
    TABLE = 'TABLE'
    TEXT = 'TEXT'
    UNIQUE = 'UNIQUE'

    #Delete query
    DELETE = 'DELETE'

    # Drop table query
    DROP = 'DROP'

    # Insert into query
    INSERT = 'INSERT INTO'
    PLACEHOLDER = '?'
    VALUES = 'VALUES'

    # Select Query
    ALL = '*'
    ASC = 'ASC'
    DESC = 'DESC'
    DISTINCT = 'DISTINCT'
    FROM = 'FROM'
    LIMIT = 'LIMIT'
    OFFSET = 'OFFSET'
    ORDER_BY = 'ORDER BY'
    SELECT = 'SELECT'
    WHERE = 'WHERE'

    #Update query
    SET = 'SET'
    UPDATE = 'UPDATE'

    # Query Operators
    AND = 'AND'
    EQ = '='
    GE = '>='
    GT = '>'
    IN = 'IN'
    LE = '<='
    LT = '<'
    OR = 'OR'
    NE = '!='
    NOT = 'NOT'

    invert = {
        EQ: NE,
        IN: ' '.join((NOT, IN)),
        EXISTS: ' '.join((NOT, EXISTS)),
    }

    def __init__(self, db_name):
        self.db_name = db_name
        self._connection = sqlite3.connect(self.db_name, isolation_level=None)
        self._connection.execute('PRAGMA foreign_keys = ON')

    def atomic(self):
        return Transaction(connection=self._connection)

    def build(self, query, values=None, read_only=False):
        raw_query = query.build()

        if read_only:
            return self.execute(raw_query, values)

        if self._connection.in_transaction:
            return self.execute(raw_query, values)

        with self.atomic():
            return self.execute(raw_query, values)

    def build_create(self, query):
        query = (
            self.CREATE, self.TABLE, self.IF, self.invert[self.EXISTS],
            query._table.lower(), str(query._fields),
        )
        return ' '.join(query)

    def build_delete(self, query):
        output = [self.DELETE, self.FROM, query._table.lower()]

        if query._filters is not None:
            output.extend((self.WHERE, str(query._filters)))

        return ' '.join(output)

    def build_drop(self, query):
        query = (
            self.DROP, self.TABLE, self.IF, self.EXISTS, query._table.lower()
        )
        return ' '.join(query)

    def build_insert(self, query):
        output = (
            self.INSERT, query._table.lower(),
            str(BracketCSV(query._fields)),
            self.VALUES,
            str(BracketCSV([self.PLACEHOLDER] * len(query._fields))),
        )
        return ' '.join(output)

    def build_select(self, query):
        output = [self.SELECT]

        if query._distinct:
            output.append(self.DISTINCT)

        fields = str(CSV(query._fields)) if query._fields else self.ALL
        output.append(fields)
        if query._tables:
            tables = (table if isinstance(table, str) else table.__name__ for table in query._tables)
            output.extend((self.FROM, str(CSV(tables)).lower()))

        if query._filters is not None:
            output.extend((self.WHERE, str(query._filters)))

        if query._limit is not None:
            output.extend((self.LIMIT, str(query._limit)))

        if query._offset is not None:
            output.extend((self.OFFSET, str(query._offset)))

        if query._order_by:
            output.extend((self.ORDER_BY, str(CSV(query._order_by))))

        return ' '.join(output)

    def build_update(self, query):
        output = [self.UPDATE, query._table.lower(), self.SET, str(CSV(query._fields))]

        if query._filters is not None:
            output.extend((self.WHERE, str(query._filters)))

        return ' '.join(output)

    def create(self):
        return CreateQuery(db=self)

    def delete(self):
        return DeleteQuery(db=self)

    def drop(self, table=None):
        query = DropQuery(db=self)
        return query if table is None else query.table(table)

    def execute(self, raw_query, values=None):
        cursor = self._connection.cursor()
        if values is None:
            return cursor.execute(raw_query)
        elif len(values) == 1:
            return cursor.execute(raw_query, values[0])
        else:
            return cursor.executemany(raw_query, values)

    def insert(self):
        return InsertQuery(db=self)

    def register(self, *args):
        try:
            for model_class in args:
                model_class._db = self
                self.create().from_model(model_class).execute()
        except TypeError:
            raise TypeError('{arg} is not a valid Model subclass.'.format(arg=model_class.__name__))

    def select(self, *args):
        return SelectQuery(db=self).select(*args)

    def update(self, *args):
        return UpdateQuery(db=self).fields(*args)


class BaseModel(type):
    def __new__(cls, clsname, bases, attrs):
        fieldnames = set()
        # Collect all field names from the base classes.
        for base in bases:
            fieldnames.update(getattr(base, '_fieldnames', []))

        fieldnames.add('pk')
        attrs['pk'] = PrimaryKeyField()

        related_fields = []
        for attr_name, attr_value in attrs.items():
            # Provide to each Field subclass the name of its attribute.
            if isinstance(attr_value, Field):
                attr_value.name = attr_name
                fieldnames.add(attr_name)
            # Keep track of each RelatedField.
            if isinstance(attr_value, ForeignKeyField):
                related_fields.append((attr_name, attr_value))

        # Add the tuple of field names as attribute of the Model class.
        attrs['_fieldnames'] = tuple(fieldnames)

        # Add instance factory class
        attrs['_factory'] = namedtuple('InstanceFactory', fieldnames)

        # Slots Model and custom Model instances
        attrs['__slots__'] = ('_values',)

        # Create the new class.
        model = super().__new__(cls, clsname, bases, attrs)

        # Each field of the class knows its related model class name.
        for fieldname in model._fieldnames:
            getattr(model, fieldname).model = model

        return model

class Node:
    __slots__ = ()

    def format(self, expression):
        return expression

    def __and__(self, other):
        return Expression(self, SQLiteDB.AND, self.format(other))

    def __eq__(self, other):
        return Expression(self, SQLiteDB.EQ, self.format(other))

    def __ge__(self, other):
        return Expression(self, SQLiteDB.GE, self.format(other))

    def __gt__(self, other):
        return Expression(self, SQLiteDB.GT, self.format(other))

    def __iand__(self, other):
        return Expression(self, SQLiteDB.AND, self.format(other))

    def __invert__(self):
        self.op = SQLiteDB.invert[self.op]
        return self

    def __le__(self, other):
        return Expression(self, SQLiteDB.LE, self.format(other))

    def __lt__(self, other):
        return Expression(self, SQLiteDB.LT, self.format(other))

    def __or__(self, other):
        return Expression(self, SQLiteDB.OR, self.format(other))

    def __ne__(self, other):
        return Expression(self, SQLiteDB.NE, self.format(other))

    def __rshift__(self, expressions):
        if not isinstance(expressions, SelectQuery):
            expressions = BracketCSV((self.format(exp) for exp in expressions))
        return Expression(self, SQLiteDB.IN, expressions)


class Expression(Node):
    __slots__ = ('lo', 'op', 'ro')

    def __init__(self, lo, op=None, ro=None):
        self.lo = lo
        self.op = op
        self.ro = ro

    def __str__(self):
        return ' '.join(str(e) for e in (self.lo, self.op, self.ro) if e is not None)


class Field(Node):
    __slots__ = ('default', 'model', 'name', 'required', 'unique', 'value')
    internal_type = None
    sqlite_datatype = None

    def __init__(self, default=None, name=None, required=True, unique=False):
        self.default = default
        self.model = None
        self.name = name
        self.required = required
        self.unique = unique
        self.value = None

        if default is not None and self.is_valid(default):
            self.default = default

    def __get__(self, instance, owner):
        """
        Default getter of a Field subclass.

        If a field is accessed through a model instance, the value of the field for this particular
        instance is returned. Insted, if a field is accessed through the model class, the Field subclass
        is returned.
        """
        if instance is not None:
            return getattr(instance._values, self.name)
        else:
            return self

    def __set__(self, instance, value):
        """
        Default setter of a Field subclass.

        The provided 'value' is stored in the hidden '_values' dictionnary of the instance,
        if the type of the value correspond to the 'internal_type' of the Fied subclass.
        Otherwise, throw a TypeError exception.

        The setter is only accessed through a model instance,
        """
        if self.is_valid(value):
            instance._values._replace(**{self.name: value})

    def __str__(self):
        return '.'.join((self.model.__name__.lower(), self.name))

    def asc(self):
        return ' '.join((str(self), self.model._db.ASC))

    def desc(self):
        return ' '.join((str(self), self.model._db.DESC))

    def is_valid(self, value):
        """Return True if the provided value match the internal field."""
        if value is not None and not isinstance(value, self.internal_type):
            raise TypeError(
                "Type of field '{field_name}' must be an instance of {internal_type}.".format(
                    field_name=self.name,
                    internal_type=self.internal_type))

        return True

    def sql(self, set_default=True):
        field_definition = [self.name, self.sqlite_datatype]

        if self.unique:
            field_definition.append(SQLiteDB.UNIQUE)

        if self.required:
            field_definition.append(SQLiteDB.NOT_NULL)

        if set_default and self.default is not None:
            field_definition.extend((SQLiteDB.DEFAULT, str(self.default)))

        return field_definition


class TextField(Field):
    __slots__ = ()
    internal_type = str
    sqlite_datatype = SQLiteDB.TEXT

    def format(self, expression):
        return ''.join(("'", expression, "'")) if isinstance(expression, str) else expression

    def sql(self):
        field_representation = super().sql(set_default=False)

        if self.default is not None:
            field_representation.extend(
                (SQLiteDB.DEFAULT, ''.join(("'", str(self.default), "'")))
            )
        return field_representation


class IntegerField(Field):
    __slots__ = ()
    internal_type = int
    sqlite_datatype = SQLiteDB.INTEGER


class FloatField(Field):
    __slots__ = ()
    internal_type = float
    sqlite_datatype = SQLiteDB.REAL


class PrimaryKeyField(IntegerField):
    __slots__ = ()

    def __init__(self, **kwargs):
       kwargs.update(required=False)
       super().__init__(**kwargs)

    def sql(self):
        return super().sql() + [SQLiteDB.PK, SQLiteDB.AUTOINCREMENT]


class ForeignKeyField(IntegerField):
    __slots__ = ('related_model', 'related_field')

    def __init__(self, related_model, related_field):
        super().__init__()
        self.related_model = related_model
        self.related_field = related_field

    def __get__(self, instance, owner):
        if instance is not None:
            related_pk_value = getattr(instance._values, self.name)
            related_pk_field = getattr(self.related_model, 'pk')
            return self.related_model.where(related_pk_field == related_pk_value)[0]
        else:
            return self

    def __set__(self, instance, value):
        """Store the primary key of a valid related model instance."""
        if self.is_valid(value):
            instance._values._replace(**{self.name: value.pk})

    def is_valid(self, value):
        if not isinstance(value, self.related_model):
            raise TypeError(
                '{value} is not an instance of {class_name}'.format(
                    value=str(value),
                    class_name=self.related_model.__name__))

        return super().is_valid(value.pk)


    def sql(self):
        return super().sql() + [SQLiteDB.REFERENCES, self.related_model.__name__.lower() + '(pk)']


class Model(metaclass=BaseModel):

    def __init__(self, **kwargs):
        # Each value for the current instance is stored in a hidden dictionary.

        for fieldname in self._fieldnames:
            if getattr(self.__class__, fieldname).required and fieldname not in kwargs:
                raise AttributeError("<{}> '{}' field is required: you need to provide a value.".format(self.__class__.__name__, fieldname))

        kwargs.setdefault('pk', None)
        self._values = self._factory(**kwargs)

    def __str__(self):
        return '{model}<{values}>'.format(
            model=self.__class__.__name__,
            values=self._values,
        )

    def __eq__(self, other):
        return self._values == other._values

    @classmethod
    def create(cls, **kwargs):
        """Return an instance of the related model."""
        last_row_id = InsertQuery(cls._db).table(cls).from_dicts(kwargs).execute()
        kwargs['pk'] = last_row_id
        return cls(**kwargs)

    @classmethod
    def create_many(cls, dicts):
        InsertQuery(db=cls._db).table(cls).from_dicts(dicts).execute()

    @classmethod
    def delete(cls, *args):
        return DeleteQuery(db=self._db).table(cls).where(*args)

    @classmethod
    def select(cls, *args):
        return SelectQuery(db=cls._db).tables(cls).select(*args)

    @classmethod
    def update(cls, *args):
        return UpdateQuery(db=cls._db).table(model).fields(*args)

    @classmethod
    def where(cls, *args):
        return SelectQuery(db=cls._db).tables(cls).where(*args)


class CreateQuery:
    __slots__ = ('_db', '_fields', '_table')

    def __init__(self, db):
        self._db = db
        self._fields = []
        self._table = None

    def __str__(self):
        return self.build()

    def build(self):
        return self._db.build_create(self)

    def execute(self):
        self._db.build(self)

    def table(self, table:str):
        self._table = table
        return self

    def fields(self, *fields):
        fields = sorted(fields, key=lambda field:field.name)
        fields = [' '.join(field.sql()) for field in fields]
        self._fields = BracketCSV(fields)
        return self

    def from_model(self, model):
        fields = [getattr(model, fieldname) for fieldname in model._fieldnames]
        return self.table(model.__name__).fields(*fields)


class FilterableQuery:
    __slots__ = ('_filters',)

    def __init__(self):
        self._filters = None

    def where(self, *filters):
        if not len(filters):
            return self

        filters = list(filters)

        if self._filters is None:
            self._filters = filters.pop()

        for expression in filters:
            self._filters &= expression

        return self


class DeleteQuery(FilterableQuery):
    """A DeleteQuery allows to forge a lazy DELETE FROM SQL query."""
    __slots__ = ('_db', '_table')

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._table = None

    def __str__(self):
        return ''.join(('(', self.build(), ')'))

    def build(self):
        return self._db.build_delete(self)

    def execute(self):
        self._db.build(self)

    def table(self, table):
        self._table = table if isinstance(table, str) else table.__name__
        return self


class DropQuery:
    __slots__ = ('_db', '_table')

    def __init__(self, db):
        self._db = db
        self._table = None

    def __str__(self):
        return self.build()

    def build(self):
        return self._db.build_drop(self)

    def execute(self):
        return self._db.build(self)

    def table(self, table):
        self._table = table if isinstance(table, str) else table.__name__
        return self


class InsertQuery:
    """An InsertQuery allows to forge a lazy INSERT INTO SQL query."""
    __slots__ = ('_db', '_fields','_table', '_values')

    def __init__(self, db):
        self._db = db
        self._fields = None
        self._table = None
        self._values = []

    def __str__(self):
        return ''.join(('(', self.build(), ')'))

    def build(self):
        return self._db.build_insert(self)

    def execute(self):
        cursor = self._db.build(self, values=self._values)
        return cursor.lastrowid

    def from_dicts(self, dicts):
        if not isinstance(dicts, list):
            dicts = [dicts]

        if self._fields is None:
            self.fields(*dicts[0].keys())

        for dct in dicts:
            self._values.append([dct[field] for field in self._fields])

        return self

    def table(self, table):
        self._table = table if isinstance(table, str) else table.__name__
        return self

    def fields(self, *fields):
        self._fields = sorted(field if isinstance(field, str) else field.name for field in fields)
        return self


class SelectQuery(FilterableQuery):
    """A SelectQuery allows to forge a lazy SELECT SQL query.

    A SelectQuery represents a Select-From-Where SQL query, and allow the user to define the WHERE
    clause. The user is allowed to add dynamically several criteria on a QuerySet. The SelectQuery only
    hit the database when it is iterated over or sliced.
    """
    __slots__ = (
        '_db', '_distinct', '_fields', '_limit', '_model',
        '_offset', '_order_by', '_tables'
    )

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._distinct = False
        self._fields = []
        self._limit = None
        self._offset = None
        self._order_by = []
        self._tables = []


    def __str__(self):
        return ''.join(('(', self.build(), ')'))

    def build(self):
        return SQLiteDB.build_select(self)

    def __iter__(self):
        """
        Allow to iterate over a SelectQuery.

        A SelectQuery can be sliced as a Python list, but with two limitations:
            - The *step* parameter is ignored
            - It is not possible to use negative indexes.

        This operation hit the database.

        Returns:
            An Iterator containing a model instance list.
                ex: Iterator(List[Pokemon])
        """
        return iter(self.get())


    def __getitem__(self, key):
        """
        Slice a SelectQuery.

        A SelectQuery can be sliced as a Python list, but with two limitations:
            - The *step* parameter is ignored
            - It is not possible to use negative indexes.

        It is similar as setting a LIMIT/OFFSET clause in a SQL query.

        This operation hit the database.

        Args:
            key: an integer representing the index or a slice object.

        Returns:
            A Model instance if the the QuerySet if accessed by index.
                ex: SelectQuery<Pokemon>[0] => Pokemon(name='Charamander)

            Otherwhise, it return a model instance list.
                ex: SelectQuery<Pokemon>[0:3] => List[Pokemon]
        """
        # Determine the offset and the number of row to return depending on the
        # type of the slice.
        try:
            offset = key.start if key.start else 0
            limit = (key.stop - offset) if key.stop is not None else -1
            direct_access = False
        except:
            limit = 1
            offset = key
            direct_access = True

        self.limit(limit)
        self.offset(offset)

        result = self.get()

        return result[0] if direct_access else result

    def build(self):
        return self._db.build_select(self)

    def dicts(self):
        """Query the database and returns the result as a list of dict"""
        cursor = self._db.build(self, read_only=True)
        rows = cursor.fetchall()
        fields = [field[0] for field in cursor.description]
        return [
            {field: value for field, value in zip(fields, row)}
            for row in rows
        ]

    def distinct(self, *fields):
        self._distinct = True
        self.select(*fields)
        return self

    def execute(self):
        """Query the database and returns the result as a list of tuples."""
        cursor = self._db.build(self, read_only=True)
        return cursor.fetchall()

    def exists(self):
        return Expression(self._db.EXISTS, self)

    def get(self):
        """Returns a list of Model instances."""
        model = self._tables[0]
        return [model(**d) for d in self.dicts()]

    def limit(self, limit:int):
        """ Slice a SelectQuery without hiting the database."""
        self._limit = limit
        return self

    def offset(self, offset:int):
        self._offset = offset
        return self

    def order_by(self, *fields):
        self._order_by.extend(field if isinstance(field, str) else str(field) for field in fields)
        return self

    def select(self, *fields):
        # Allow to filter Select-Query on columns.
        self._fields.extend(field if isinstance(field, str) else str(field) for field in fields)
        return self

    def tables(self, *tables):
        self._tables.extend(tables)
        return self


class UpdateQuery(FilterableQuery):
    __slots__ = ('_db', '_fields', '_table')

    def __init__(self, db):
        super().__init__()
        self._db = db
        self._table = None
        self._fields = []

    def __str__(self):
        return ''.join(('(', self.build(), ')'))

    def build(self):
        return self._db.build_update(self)

    def execute(self):
        return self._db.build(self)

    def fields(self, *args):
        # Remove table name in each Expression left operand.
        for expression in args:
            if isinstance(expression.lo, Field):
                expression.lo = expression.lo.name

        self._fields.extend(args)
        return self

    def table(self, table):
        self._table = table if isinstance(table, str) else table.__name__
        return self
