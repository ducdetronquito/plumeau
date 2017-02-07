from collections import deque, namedtuple
from contextlib import closing
import sqlite3

__all__ = [
    'Database', 'Field', 'FloatField', 'ForeignKeyField', 'IntegerField',
    'Model', 'PrimaryKeyField', 'TextField',
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


class SQLiteAPI:
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
    DISTINCT = 'DISTINCT'
    FROM = 'FROM'
    LIMIT = 'LIMIT'
    OFFSET = 'OFFSET'
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

    @classmethod
    def create_table(cls, name, fields):
        query = (
            cls.CREATE, cls.TABLE, cls.IF, cls.invert[cls.EXISTS],
            name.lower(), str(fields),
        )
        return ' '.join(query)

    @classmethod
    def delete(cls, query):
        output = [cls.DELETE, cls.FROM, query._table.lower()]

        if query._filters is not None:
            output.extend((cls.WHERE, str(query._filters)))

        return ' '.join(output)

    @classmethod
    def drop_table(cls, name):
        query = (
            cls.DROP, cls.TABLE, cls.IF, cls.EXISTS, name.lower()
        )
        return ' '.join(query)

    @classmethod
    def insert_into(cls, query):
        output = (
            cls.INSERT, query._table.lower(),
            str(query._fields),
            cls.VALUES,
            str(BracketCSV([cls.PLACEHOLDER] * len(query._fields))),
        )
        return ' '.join(output)

    @classmethod
    def select(cls, query):
        output = [cls.SELECT]
        
        if query._distinct:
            output.append(cls.DISTINCT)
            
        fields = str(query._fields) if query._fields else cls.ALL  
        output.extend((fields, cls.FROM, str(query._tables).lower()))
        
        if query._filters is not None:
            output.extend((cls.WHERE, str(query._filters)))

        if query._count is not None and query._offset is not None:
            output.extend((cls.LIMIT, str(query._count), cls.OFFSET, str(query._offset)))
        
        return' '.join(output)

    @classmethod
    def update(cls, query):
        output = [cls.UPDATE, query._table.lower(), cls.SET, str(CSV(query._fields))]

        if query._filters is not None:
            output.extend((cls.WHERE, str(query._filters)))

        return ' '.join(output)


class FilterableQuery:
    __slots__ = ('_filters',)

    def __init__(self, filters=None):
        self._filters = filters

    def where(self, *args):
        if not len(args):
            return self

        args = list(args)

        if self._filters is None:
            self._filters = args.pop()

        for expression in args:
            self._filters &= expression

        return self


class DeleteQuery(FilterableQuery):
    """A DeleteQuery allows to forge a lazy DELETE FROM SQL query."""
    __slots__ = ('_model', '_table')

    def __init__(self, model, where=None):
        super().__init__(where)
        self._model = model
        self._table = model.__name__

    def __str__(self):
        return ''.join(('(', SQLiteAPI.delete(self), ')'))

    def execute(self):
        self._model._db.delete(self)


class InsertQuery:
    """An InsertQuery allows to forge a lazy INSERT INTO SQL query."""
    __slots__ = ('_fields', '_model', '_table', '_values')

    def __init__(self, model):
        self._model = model
        self._table = model.__name__
        self._fields = None
        self._values = []
    
    def __str__(self):
        return ''.join(('(', SQLiteAPI.insert_into(self), ')'))

    def execute(self):
        return self._model._db.insert_into(self)

    def with_fields(self, *fields):
        self._fields = BracketCSV(fields)
        return self

    def from_dicts(self, dicts):
        if not isinstance(dicts, list):
            dicts = [dicts]
        
        self._fields = self._fields or BracketCSV(dicts[0].keys())

        for dct in dicts:
            self._values.append([dct[field] for field in self._fields])
        
        return self
        

class SelectQuery(FilterableQuery):
    """A SelectQuery allows to forge a lazy SELECT SQL query.

    A SelectQuery represents a Select-From-Where SQL query, and allow the user to define the WHERE
    clause. The user is allowed to add dynamically several criteria on a QuerySet. The SelectQuery only
    hit the database when it is iterated over or sliced.
    """
    __slots__ = ('_count', '_distinct', '_fields', '_model', '_offset', '_tables')

    def __init__(self, model, fields=None, where=None):
        super().__init__(where)
        self._model = model
        self._tables = CSV([model.__name__])
        self._fields = fields
        self._count = None
        self._offset = None
        self._distinct = False

    def __str__(self):
        return ''.join(('(', SQLiteAPI.select(self), ')'))

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
            count = (key.stop - offset) if key.stop is not None else -1
            direct_access = False
        except:
            count = 1
            offset = key
            direct_access = True

        self.limit(count, offset)

        result = self.get()

        return result[0] if direct_access else result

    def _execute(self):
        """Query the database and returns the result as a list of tuples."""
        return self._model._db.select(self)

    def get(self):
        """Returns a list of Model instances."""
        return [self._model(**d) for d in self.dicts()]

    def dicts(self, allow_fields_subset=True):
        """Query the database and returns the result as a list of dict"""
        fields = [field.name for field in self._fields] if self._fields else self._model._fieldnames

        return [
            {fieldname: value for fieldname, value in zip(fields, row)}
            for row in self._execute()
        ]
    
    def distinct(self, *fields):
        self._distinct = True
        self.select(*fields)
        return self

    def limit(self, count, offset):
        """ Slice a SelectQuery without hiting the database."""
        self._count = count
        self._offset = offset

        return self

    def select(self, *args):
        # Allow to filter Select-Query on columns.
        self._fields = CSV(args)
        return self

    def tuples(self, named=False):
        """Output a SelectQuery as a list of tuples or namedtuples"""
        if not named:
            return self._execute()
        
        if self._fields:
            fields = CSV(field.name for field in self._fields)
        else:
            fields = CSV(self._model._fieldnames)
        
        factory = namedtuple('factory', fields)
        return [factory._make(row) for row in self._execute()]


class UpdateQuery(FilterableQuery):
    __slots__ = ('_fields', '_model', '_table')

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._table = model.__name__
        self._fields = []

    def __str__(self):
        return ''.join(('(', SQLiteAPI.update(self), ')'))

    def execute(self):
        return self._model._db.update(self)#self._table, CSV(self._set), self._where)

    def set(self, *args):
        # Remove table name in each Expression left operand.
        for expression in args:
            if isinstance(expression.lo, Field):
                expression.lo = expression.lo.name

        self._fields.extend(args)
        return self


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
        new_class = super().__new__(cls, clsname, bases, attrs)

        # Each field of the class knows its related model class name.
        for fieldname in new_class._fieldnames:
            getattr(new_class, fieldname).model_name = clsname.lower()

        return new_class

class Node:
    __slots__ = ()

    def format(self, expression):
        return expression

    def __and__(self, other):
        return Expression(self, SQLiteAPI.AND, self.format(other))

    def __eq__(self, other):
        return Expression(self, SQLiteAPI.EQ, self.format(other))

    def __ge__(self, other):
        return Expression(self, SQLiteAPI.GE, self.format(other))

    def __gt__(self, other):
        return Expression(self, SQLiteAPI.GT, self.format(other))

    def __iand__(self, other):
        return Expression(self, SQLiteAPI.AND, self.format(other))

    def __invert__(self):
        self.op = SQLiteAPI.invert[self.op]
        return self

    def __le__(self, other):
        return Expression(self, SQLiteAPI.LE, self.format(other))

    def __lt__(self, other):
        return Expression(self, SQLiteAPI.LT, self.format(other))

    def __or__(self, other):
        return Expression(self, SQLiteAPI.OR, self.format(other))

    def __ne__(self, other):
        return Expression(self, SQLiteAPI.NE, self.format(other))

    def __rshift__(self, expressions):
        if not isinstance(expressions, SelectQuery):
            expressions = BracketCSV((self.format(exp) for exp in expressions))
        return Expression(self, SQLiteAPI.IN, expressions)


class Expression(Node):
    __slots__ = ('lo', 'op', 'ro')

    def __init__(self, lo, op=None, ro=None):
        self.lo = lo
        self.op = op
        self.ro = ro

    def __str__(self):
        return ' '.join(str(e) for e in (self.lo, self.op, self.ro) if e is not None)


class Field(Node):
    __slots__ = ('default', 'model_name', 'name', 'required', 'unique', 'value')
    internal_type = None
    sqlite_datatype = None

    def __init__(self, required=True, unique=False, default=None):
        self.default = default
        self.model_name = None
        self.name = None
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
        return '.'.join((self.model_name, self.name))

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
            field_definition.append(SQLiteAPI.UNIQUE)

        if self.required:
            field_definition.append(SQLiteAPI.NOT_NULL)

        if set_default and self.default is not None:
            field_definition.extend((SQLiteAPI.DEFAULT, str(self.default)))

        return field_definition


class TextField(Field):
    __slots__ = ()
    internal_type = str
    sqlite_datatype = SQLiteAPI.TEXT

    def format(self, expression):
        return ''.join(("'", expression, "'")) if isinstance(expression, str) else expression

    def sql(self):
        field_representation = super().sql(set_default=False)

        if self.default is not None:
            field_representation.extend(
                (SQLiteAPI.DEFAULT, ''.join(("'", str(self.default), "'")))
            )
        return field_representation


class IntegerField(Field):
    __slots__ = ()
    internal_type = int
    sqlite_datatype = SQLiteAPI.INTEGER


class FloatField(Field):
    __slots__ = ()
    internal_type = float
    sqlite_datatype = SQLiteAPI.REAL


class PrimaryKeyField(IntegerField):
    __slots__ = ()

    def __init__(self, **kwargs):
       kwargs.update(required=False)
       super().__init__(**kwargs)

    def sql(self):
        return super().sql() + [SQLiteAPI.PK, SQLiteAPI.AUTOINCREMENT]


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
        return super().sql() + [SQLiteAPI.REFERENCES, self.related_model.__name__.lower() + '(pk)']


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
        last_row_id = InsertQuery(model=cls).from_dicts(kwargs).execute()
        kwargs['pk'] = last_row_id
        return cls(**kwargs)
    
    @classmethod
    def create_many(cls, dicts):
        InsertQuery(model=cls).from_dicts(dicts).execute()
        
    @classmethod
    def delete(cls, *args):
        return DeleteQuery(model=cls).where(*args)

    @classmethod
    def select(cls, *args):
        return SelectQuery(model=cls).select(*args)

    @classmethod
    def update(cls, *args):
        return UpdateQuery(model=cls).set(*args)

    @classmethod
    def where(cls, *args):
        return SelectQuery(model=cls).where(*args)


class Database:
    __slots__ = ('db_name', '_connection')

    def __init__(self, db_name):
        self.db_name = db_name
        self._connection = sqlite3.connect(self.db_name)
        self._connection.execute('PRAGMA foreign_keys = ON')

    def drop_table(self, model_class):
        query = SQLiteAPI.drop_table(model_class.__name__)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()

    def create_table(self, model_class):
        fields = BracketCSV((
            ' '.join(getattr(model_class, fieldname).sql())
            for fieldname in model_class._fieldnames
        ))

        query = SQLiteAPI.create_table(model_class.__name__, fields)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()

    def delete(self, query):
        query = SQLiteAPI.delete(query)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()
        
    def insert_into(self, query):
        return self.insert_many(query) if len(query._values) > 1 else self.insert_one(query)

    def insert_one(self, query):
        raw_query = SQLiteAPI.insert_into(query)
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(raw_query, query._values[0])
            last_row_id = cursor.lastrowid
            self._connection.commit()
        return last_row_id

    def insert_many(self, query):
        raw_query = SQLiteAPI.insert_into(query)
        with closing(self._connection.cursor()) as cursor:
            cursor.executemany(raw_query, query._values)
            self._connection.commit()
        
    def select(self, query):
        query = SQLiteAPI.select(query)

        with closing(self._connection.cursor()) as cursor:
            return cursor.execute(query).fetchall()

    def update(self, query):
        query = SQLiteAPI.update(query)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()

    def register(self, *args):
        try:
            for model_class in args:
                model_class._db = self
                self.create_table(model_class)
        except TypeError:
            raise TypeError('{arg} is not a valid Model subclass.'.format(arg=model_class.__name__))

