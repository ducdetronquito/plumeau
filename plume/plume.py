from collections import deque, namedtuple
from contextlib import closing
import sqlite3

__all__ = [
    'Database', 'Field', 'FloatField', 'ForeignKeyField', 'IntegerField',
    'Model', 'PrimaryKeyField', 'TextField',
]


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
            name.lower(), cls.to_csv(fields, bracket=True),
        )
        return ' '.join(query)
    
    @classmethod
    def delete(cls, table, where=None):
        query = [cls.DELETE, cls.FROM, table.lower()]
        
        if where is not None:
            query.extend((cls.WHERE, str(where)))
        
        return ' '.join(query)

    @classmethod
    def drop_table(cls, name):
        query = (
            cls.DROP, cls.TABLE, cls.IF, cls.EXISTS, name.lower()
        )
        return ' '.join(query)

    @classmethod
    def insert_into(cls, table_name, field_names):
        query = (
            cls.INSERT, table_name.lower(),
            cls.to_csv(field_names, bracket=True),
            cls.VALUES,
            cls.to_csv([cls.PLACEHOLDER] * len(field_names), bracket=True)
        )
        return ' '.join(query)

    @classmethod
    def select(cls, tables, fields=None, where=None, count=None, offset=None):
        query = [
            cls.SELECT, cls.to_csv(fields or cls.ALL).lower(),
            cls.FROM, cls.to_csv(tables).lower(),
        ]

        if where is not None:
            query.extend((cls.WHERE, str(where)))

        if count is not None and offset is not None:
            query.extend((cls.LIMIT, str(count), cls.OFFSET, str(offset)))
        return ' '.join(query)

    @classmethod
    def update(cls, table_name, fields, where=None):
        query = [
            cls.UPDATE, table_name.lower(), cls.SET, cls.to_csv(str(fields), bracket=False)
        ]
        
        if where is not None:
            query.extend((cls.WHERE, str(where)))
        
        return ' '.join(query)
    
    @staticmethod
    def to_csv(values, bracket=False):
        """Convert a string value or a sequence of string values into a coma-separated string."""
        try:
            values = values.split()
        except AttributeError:
            pass

        csv = ', '.join(values)

        return '(' + csv + ')' if bracket else csv


class Node:
    __slots__ = ()

    @staticmethod
    def check(value):
        # TODO: change the method name with a more explicit one.
        if isinstance(value, str):
            # The value is a string litteral, and must be quoted.
            return ''.join(("'", value, "'"))
        elif isinstance(value, list):
            # The value is a list of litterals, and is turned into a tuple.
            # This allows to have a valid SQL list just by calling str(value)
            return tuple(value)
        else:
            return value

    def __and__(self, other):
        return Expression(self, SQLiteAPI.AND, Node.check(other))

    def __eq__(self, other):
        return Expression(self, SQLiteAPI.EQ, Node.check(other))

    def __ge__(self, other):
        return Expression(self, SQLiteAPI.GE, Node.check(other))

    def __gt__(self, other):
        return Expression(self, SQLiteAPI.GT, Node.check(other))

    def __iand__(self, other):
        return Expression(self, SQLiteAPI.AND, Node.check(other))

    def __invert__(self):
        self.op = SQLiteAPI.invert[self.op]
        return self

    def __le__(self, other):
        return Expression(self, SQLiteAPI.LE, Node.check(other))

    def __lshift__(self, other):
        return Expression(self, SQLiteAPI.IN, Node.check(other))

    def __lt__(self, other):
        return Expression(self, SQLiteAPI.LT, Node.check(other))

    def __or__(self, other):
        return Expression(self, SQLiteAPI.OR, Node.check(other))

    def __ne__(self, other):
        return Expression(self, SQLiteAPI.NE, Node.check(other))


class Expression(Node):
    __slots__ = ('lo', 'op', 'ro')

    def __init__(self, lo, op=None, ro=None):
        self.lo = lo
        self.op = op
        self.ro = ro

    def __str__(self):
        return ' '.join((str(e) for e in (self.lo, self.op, self.ro) if e is not None))


class FilterableQuery:
    __slots__ = ('_where',)
    
    def __init__(self, where=None):
        self._where = where

    def where(self, *args):
        if not len(args):
            return self

        args = list(args)
        
        if self._where is None:
            self._where = args.pop()

        for expression in args:
            self._where &= expression

        return self


class DeleteQuery(FilterableQuery):
    """A DeleteQuery allows to forge a lazy DELETE FROM SQL query."""
    __slots__ = ('_model', '_table')
    
    def __init__(self, model, where=None):
        super().__init__(where)
        self._model = model
        self._table = model.__name__.lower()
    
    def __str__(self):
        return ''.join(
            ('(', SQLiteAPI.delete(self._table, self._where), ')')
        )

    def execute(self):
        self._model._db.delete(self._table, self._where)


class SelectQuery(FilterableQuery):
    """A SelectQuery allows to forge a lazy SELECT SQL query.

    A SelectQuery represents a Select-From-Where SQL query, and allow the user to define the WHERE
    clause. The user is allowed to add dynamically several criteria on a QuerySet. The SelectQuery only
    hit the database when it is iterated over or sliced.
    """
    __slots__ = ('_model', '_tables', '_fields', '_count', '_offset')

    def __init__(self, model, fields=None, where=None):
        super().__init__(where)
        self._model = model
        self._tables = [model.__name__.lower()]
        self._fields = fields
        self._count = None
        self._offset = None

    def __str__(self):
        return ''.join((
            '(', SQLiteAPI.select(
                self._tables, self._fields, self._where, self._count, self._offset), ')'
        ))

    def select(self, *args):
        # Allow to filter Select-Query on columns.
        self._fields = [str(field) for field in args]
        return self

    def limit(self, count, offset):
        """ Slice a SelectQuery without hiting the database."""
        self._count = count
        self._offset = offset

        return self

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
        return iter(self.execute())


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

        result = self.execute()

        return result[0] if direct_access else result

    def _execute(self):
        """Query the database and returns the result as a list of tuples."""
        return self._model._db.select(
            self._tables, self._fields, self._where, self._count, self._offset,
        )

    def dicts(self, allow_fields_subset=True):
        """Query the database and returns the result as a list of dict"""
        fields = self._fields or self._model._fieldnames

        return [
            {fieldname: value for fieldname, value in zip(fields, row)}
            for row in self._execute()
        ]

    def execute(self):
        """Returns a list of Model instances."""
        return [self._model(**d) for d in self.dicts()]

    def tuples(self, named=False):
        """Output a SelectQuery as a list of tuples or namedtuples"""
        if not named:
            return self._execute()

        fields =  self._fields or self._model._fieldnames
        factory = namedtuple('factory', fields)
        return [factory._make(row) for row in self._execute()]


class UpdateQuery(FilterableQuery):
    __slots__ = ('_model', '_table', '_fields')

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._table = model.__name__.lower()
        self._fields = None
        
    def __str__(self):
        return ''.join(
            ('(', SQLiteAPI.update(self._table, self._fields, self._where), ')')
        )
    
    def execute(self):
        return self._model._db.update(
            self._table, self._fields, self._where
        )

    def set(self, *args):
        self._fields = self._fields or []
        self._fields.extend((str(arg) for arg in args))
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
        return super().sql() + ['REFERENCES', self.related_model.__name__.lower() + '(pk)']


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
        field_names = [fieldname for fieldname in cls._fieldnames if fieldname in kwargs]
        values = [kwargs[fieldname] for fieldname in cls._fieldnames if fieldname in kwargs]

        values = [value.pk if isinstance(value, Model) else value for value in values]

        query = SQLiteAPI.insert_into(cls.__name__, field_names)

        last_row_id = cls._db.insert_into(query, values)
        kwargs =  {field: value for field, value in zip(field_names, values)}
        kwargs['pk'] = last_row_id
        instance = cls(**kwargs)

        return instance

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
        fields = [
            ' '.join(getattr(model_class, fieldname).sql())
            for fieldname in model_class._fieldnames
        ]

        query = SQLiteAPI.create_table(model_class.__name__, fields)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()

    def delete(self, table, where=None):
        query = SQLiteAPI.delete(table, where)
        
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query)
            self._connection.commit()
        
    def insert_into(self, query, values):
        last_row_id = None

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query, values)
            last_row_id = cursor.lastrowid
            self._connection.commit()

        return last_row_id

    def select(self, tables, fields=None, where=None, count=None, offset=None):
        query = SQLiteAPI.select(tables, fields, where, count, offset)

        with closing(self._connection.cursor()) as cursor:
            return cursor.execute(query).fetchall()

    def update(self, table, fields, where=None):
        query = SQLiteAPI.update(table, fields, where)
        
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

