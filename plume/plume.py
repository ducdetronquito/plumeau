from collections import deque, namedtuple
from contextlib import closing
import sqlite3

__all__ = [
    'Database', 'Field', 'FloatField', 'ForeignKeyField', 'IntegerField', 'Model',
    'NumericField', 'PrimaryKeyField', 'TextField',
]


class SQLiteAPI:
    # Create table query
    AUTOINCREMENT = 'AUTOINCREMENT'
    CREATE = 'CREATE TABLE'
    DEFAULT = 'DEFAULT'
    IF_NOT_EXISTS = 'IF NOT EXISTS'
    INTEGER = 'INTEGER'
    NOT_NULL = 'NOT NULL'
    PK = 'PRIMARY KEY'
    REAL = 'REAL'
    TEXT = 'TEXT'
    UNIQUE = 'UNIQUE'
    
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

    @classmethod
    def create_table(cls, name, fields):
        query = [
            SQLiteAPI.CREATE, SQLiteAPI.IF_NOT_EXISTS, name.lower(), 
            SQLiteAPI.to_csv(fields, bracket=True),
        ]
        
        return ' '.join(query)
    
    @classmethod
    def insert_into(cls, table_name, field_names):
        query = [
            SQLiteAPI.INSERT, table_name.lower(),
            SQLiteAPI.to_csv(field_names, bracket=True),
            SQLiteAPI.VALUES, 
            SQLiteAPI.to_csv([SQLiteAPI.PLACEHOLDER] * len(field_names), bracket=True)
        ]
        
        return " ".join(query)

    @classmethod
    def select(cls, tables, fields=None, where=None, count=None, offset=None):
        query = []
        
        query.extend((
            SQLiteAPI.SELECT, SQLiteAPI.to_csv(fields or SQLiteAPI.ALL).lower(),
        ))
        
        query.extend((
            SQLiteAPI.FROM, SQLiteAPI.to_csv(tables).lower(),
        ))
        
        if where is not None:
            query.extend((
                SQLiteAPI.WHERE, str(where),
            ))
            
        if count is not None and offset is not None:
            query.extend((
                SQLiteAPI.LIMIT, str(count), SQLiteAPI.OFFSET, str(offset),
            ))
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


class Clause(deque):
    __slots__ = ()

    def __init__(self, value=None):
        if value is not None:
            self.append(value)
    
    def __and__(self, other):
        clause = ' '.join((str(other), SQLiteAPI.AND)) if len(self) else str(other)
            
        self.appendleft(clause)
        return self
    
    def __or__(self, other):
        self.appendleft('(')
        self.append(' '.join((SQLiteAPI.OR, str(other), ')')))
        return self
        
    def __str__(self):
        return ' '.join((e for e in self))


class Criterion:
    __slots__= ('field', 'operator', 'value')
    
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def __str__(self):
        return ' '.join((self.field, self.operator, str(self.value)))
        
    def __and__(self, other):
        return Clause(' '.join((str(self), SQLiteAPI.AND, str(other))))

    def __or__(self, other):
        return Clause(' '.join(( '(', str(self), SQLiteAPI.OR, str(other), ')')))


class QuerySet:
    """A QuerySet allows to forge a lazy SQL query.

    A QuerySet represents a Select-From-Where SQL query, and allow the user to define the WHERE
    clause. The user is allowed to add dynamically several criteria on a QuerySet. The QuerySet only
    hit the database when it is iterated over or sliced.
    """
    __slots__ = ('_model', '_tables', '_fields', '_clause', '_count', '_offset')
    
    def __init__(self, model):
        self._model = model
        self._tables = [model.__name__.lower()]
        self._fields = None
        self._clause = None
        self._count = None
        self._offset = None
    
    def __str__(self):
        return ''.join((
            '(', SQLiteAPI.select(
                self._tables, self._fields, self._clause, self._count, self._offset), ')'
        ))

    def filter(self, *args):
        """
        Allow to filter a QuerySet.
        
        A QuerySet can filter as a Python list to select a subset of model instances.
        It is similar as setting a WHERE clause in a SQL query.
        
        This operation does not hit the database.
        
        Args:
            args: a list of Criterion represented in a conjonctive normal form.
        
        Returns:
            A QuerySet
        """
        if args:
            self._clause = self._clause or Clause()
            
            for element in args:
                self._clause &= element

        return self
        
    def select(self, *args):
        # Allow to filter Select-Query on columns.
        self._fields = args

        return self

    def slice(self, count, offset):
        """ Slice a QuerySet without hiting the database."""
        self._count = count
        self._offset = offset

        return self
        
    def __execute(self):
        """Query the database and returns the result."""
        rows = self._model._db.select(
            self._tables, self._fields, self._clause, self._count, self._offset
        )
        
        if self._fields is not None:
            # If several fields are specified, returns a list of tuples,
            # each containing a value for each field.
            # If only one field is specified, returns a list of value for that field.
            if len(self._fields) > 1:
                return iter(rows)
                
            return iter([row[0] for row in rows])
        
        # If no field restriction is provided, returns a list of Model instance.
        return iter([
            self._model(**{
                fieldname: value for fieldname, value in zip(self._model._fieldnames, row)
            })
            for row in rows
        ])

    def __iter__(self):
        """
        Allow to iterate over a QuerySet.
        
        A QuerySet can be sliced as a Python list, but with two limitations:
            - The *step* parameter is ignored
            - It is not possible to use negative indexes.
        
        This operation hit the database.
        
        Returns:
            An Iterator containing a model instance list.
                ex: Iterator(List[Pokemon])
        """
        return self.__execute()
    
    def __getitem__(self, key):
        """
        Slice a QuerySet.
        
        A QuerySet can be sliced as a Python list, but with two limitations:
            - The *step* parameter is ignored
            - It is not possible to use negative indexes.
        
        It is similar as setting a LIMIT/OFFSET clause in a SQL query.
        
        This operation hit the database.
        
        Args:
            key: an integer representing the index or a slice object.
            
        Returns:
            A Model instance if the the QuerySet if accessed by index.
                ex: QuerySet<Pokemon>[0] => Pokemon(name='Charamander)
            
            Otherwhise, it return a model instance list.
                ex: QuerySet<Pokemon>[0:3] => List[Pokemon]
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
        
        self.slice(count, offset)
            
        result = self.__execute()
        
        return list(result)[0] if direct_access else list(result)


class Manager:
    __slots__ = ('_model',)
    
    def __init__(self, model):
        self._model = model

    def __get__(self, instance, owner):
        # A Model Manager is only accessible as a class attribute.
        if instance is None:
            return self

    def create(self, **kwargs):
        """Return an instance of the related model."""
        field_names = [fieldname for fieldname in self._model._fieldnames if fieldname in kwargs]
        values = [kwargs[fieldname] for fieldname in self._model._fieldnames if fieldname in kwargs]
        
        values = [value.pk if isinstance(value, Model) else value for value in values]
                
        query = SQLiteAPI.insert_into(self._model.__name__, field_names)
        
        last_row_id = self._model._db.insert_into(query, values)
        kwargs =  {field: value for field, value in zip(field_names, values)}
        kwargs['pk'] = last_row_id
        instance = self._model(**kwargs)
    
        return instance
        
    def select(self, *args):
        return QuerySet(self._model).select(*args)

    def filter(self, *args):
        return QuerySet(self._model).filter(*args)


class RelatedManager(Manager):
    __slots__ = ()

    def __get__(self, instance, owner):
        # A RelatedManager is only accessible as an instance attribute.
        if instance is not None:
            return self


class BaseModel(type):
    def __new__(cls, clsname, bases, attrs):
        fieldnames = []
        # Collect all field names from the base classes.
        for base in bases:
            fieldnames.extend(getattr(base, '_fieldnames', []))

        related_fields = []
        for attr_name, attr_value in attrs.items():
            # Provide to each Field subclass the name of its attribute.
            if isinstance(attr_value, Field):
                attr_value.name = attr_name
                fieldnames.append(attr_name)
            # Keep track of each RelatedField. 
            if isinstance(attr_value, ForeignKeyField):
                related_fields.append((attr_name, attr_value))
        
        # Add the list of field names as attribute of the Model class.
        attrs['_fieldnames'] = fieldnames 
        
        # Add instance factory class
        attrs['_factory'] = namedtuple('InstanceFactory', fieldnames)
        
        # Slots Model and custom Model instances
        attrs['__slots__'] = ('_values',)
        
        # Create the new class.
        new_class = super().__new__(cls, clsname, bases, attrs)
        
        #Add a Manager instance as an attribute of the Model class.
        setattr(new_class, 'objects', Manager(new_class))
       
        # Add a Manager to each related Model.
        for attr_name, attr_value in related_fields:
            setattr(attr_value.related_model, attr_value.related_field, RelatedManager(new_class))
         
        return new_class


class Field:
    __slots__ = ('value', 'name', 'required', 'unique', 'default')
    internal_type = None
    sqlite_datatype = None

    def __init__(self, required=True, unique=False, default=None):
        self.value = None
        self.name = None
        self.required = required
        self.unique = unique
        self.default = None
        
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
    
    def __eq__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.EQ, ''.join(("'", other, "'")))

    def __ne__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.NE, ''.join(("'", other, "'")))


    def __lshift__(self, other):
        """IN operator."""
        if all((self.is_valid(e) for e in other)):
            values = (''.join(("'", str(e), "'")) for e in other)
            return Criterion(self.name, SQLiteAPI.IN, SQLiteAPI.to_csv(values, bracket=True))

    def sql(self):
        field_representation = super().sql(set_default=False)
        
        if self.default is not None:
            field_representation.extend(
                (SQLiteAPI.DEFAULT, ''.join(("'", str(self.default), "'")))
            )
        return field_representation

class NumericField(Field):
    __slots__ = ()

    def __eq__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.EQ, other)

    def __ne__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.NE, other)

    def __lt__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.LT, other)

    def __le__(self, other):
        if self.is_valid(other): 
            return Criterion(self.name, SQLiteAPI.LE, other)

    def __gt__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.GT, other)

    def __ge__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, SQLiteAPI.GE, other)
    
    def __lshift__(self, other):
        """IN operator."""
        if all((self.is_valid(e) for e in other)):
            values = (str(e) for e in other)
            return Criterion(self.name, SQLiteAPI.IN, SQLiteAPI.to_csv(values, bracket=True))


class IntegerField(NumericField):
    __slots__ = ()
    internal_type = int    
    sqlite_datatype = SQLiteAPI.INTEGER


class FloatField(NumericField):
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
            return self.related_model.objects.filter(related_pk_field == related_pk_value)[0]
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
    pk = PrimaryKeyField()

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


class Database:
    __slots__ = ('db_name', '_connection')

    def __init__(self, db_name):
        self.db_name = db_name
        self._connection = sqlite3.connect(self.db_name)
        self._connection.execute('PRAGMA foreign_keys = ON')
   
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

    def create_table(self, model_class):
        fields = [
            ' '.join(getattr(model_class, fieldname).sql())
            for fieldname in model_class._fieldnames
        ]
        
        query = SQLiteAPI.create_table(model_class.__name__, fields)

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

