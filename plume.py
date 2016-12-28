from collections import deque
from contextlib import closing
from copy import deepcopy
import sqlite3

"""
To do:
    - Handle ORDER BY
    - Handle query operations (Count, Sum)
    - Add tests all classes
    - Comply to PEP8 and Google Python Style Guide as much as possible.
    - Handle Foreign Keys T_T
"""

class SQLiteAPI:
    AND = ' AND '
    AUTOINCREMENT = 'AUTOINCREMENT'
    CREATE = 'CREATE TABLE '
    DEFAULT = 'DEFAULT '
    FROM = ' FROM '
    IF_NOT_EXISTS = 'IF NOT EXISTS '
    INSERT = 'INSERT INTO'
    INTEGER = 'INTEGER'
    LIMIT = ' LIMIT '
    NOT_NULL = 'NOT NULL'
    OFFSET = ' OFFSET '
    OR = ' OR '
    PK = 'PRIMARY KEY'
    REAL = 'REAL'
    SELECT = 'SELECT '
    TEXT = 'TEXT'
    UNIQUE = 'UNIQUE '
    VALUES = 'VALUES'
    WHERE = ' WHERE '
    
    # Query Operators
    EQ = '='
    GE = '>='
    GT = '>'
    IN = 'IN'
    LE = '<='
    LT = '<'
    NE = '!='


    @classmethod
    def create_table(cls, name, fields):
        query = [
            SQLiteAPI.CREATE, SQLiteAPI.IF_NOT_EXISTS, name.lower(), 
            SQLiteAPI.to_csv(fields, bracket=True),
        ]
        
        return ''.join(query)
    
    @classmethod
    def insert_into(cls, table_name, field_names):
        query = [
            SQLiteAPI.INSERT, table_name.lower(), SQLiteAPI.to_csv(field_names, bracket=True),
            SQLiteAPI.VALUES, SQLiteAPI.to_csv(['?'] * len(field_names), bracket=True)
        ]
        
        return ' '.join(query)

    @classmethod
    def select(cls, tables, fields=None, where=None, count=None, offset=None):
        query = []
        
        query.extend((
            SQLiteAPI.SELECT, SQLiteAPI.to_csv(fields or '*').lower(),
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
        
        return ''.join(query)
    
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
    
    def __init__(self, value=None):
        if value is not None:
            self.append(value)
    
    def __and__(self, other):
        clause = ''.join((str(other), SQLiteAPI.AND)) if len(self) else str(other)
            
        self.appendleft(clause)
        return self
    
    def __or__(self, other):
        self.appendleft('(')
        self.append(''.join((SQLiteAPI.OR, str(other), ')')))
        return self
        
    def __str__(self):
        return ''.join((e for e in self))


class Criterion:
    
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def __str__(self):
        return ' '.join((self.field, self.operator, str(self.value)))
        
    def __and__(self, other):
        return Clause(''.join((str(self), SQLiteAPI.AND, str(other))))

    def __or__(self, other):
        return Clause(''.join(( '(', str(self), SQLiteAPI.OR, str(other), ')')))


class QuerySet:
    """A QuerySet allows to forge a lazy SQL query.

    A QuerySet represents a Select-From-Where SQL query, and allow the user to define the WHERE
    clause. The user is allowed to add dynamically several criteria on a QuerySet. The QuerySet only
    hit the database when it is iterated over or sliced.
    """
    
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
        
    def slice(self, count, offset):
        """ Slice a QuerySet without hiting the database."""
        self._count = count
        self._offset = offset

        return self
        
    def __execute(self):
        """Query the database and returns the result as a list of model instances."""
        values = self._model._db.select(
            self._tables, self._fields, self._clause, self._count, self._offset
        )
        
        return iter([
            self._model(**{
                fieldname: value for fieldname, value in zip(self._model._fieldnames, instance)
            })
            for instance in values
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

    def __init__(self, model):
        self._model = model
        self._queryset = None

    def __get__(self, instance, owner):
        # A Model Manager is only accessible as a class attribute.
        if instance is None:
            return self

    def create(self, **kwargs):
        """Return an instance of the related model.""" 
        field_names = [fieldname for fieldname in self._model._fieldnames if fieldname in kwargs]
        values = [kwargs[fieldname] for fieldname in self._model._fieldnames if fieldname in kwargs]
        
        query = SQLiteAPI.insert_into(self._model.__name__, field_names)
        
        last_row_id = self._model._db.insert_into(query, values)
        kwargs =  {field: value for field, value in zip(field_names, values)}
        instance = self._model(**kwargs)
        instance.pk = last_row_id
        
        return instance

    def filter(self, *args):
        return QuerySet(self._model).filter(*args)


class RelatedManager(Manager):
    
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
            if isinstance(attr_value, BaseField):
                attr_value.name = attr_name
                fieldnames.append(attr_name)
            # Keep track of each RelatedField. 
            if isinstance(attr_value, ForeignKeyField):
                related_fields.append((attr_name, attr_value))
        
        # Add the list of field names as attribute of the Model class.
        attrs['_fieldnames'] = fieldnames 
       
        # Create the new class.
        new_class = super().__new__(cls, clsname, bases, attrs)
        
        #Add a Manager instance as an attribute of the Model class.
        setattr(new_class, 'objects', Manager(new_class))
       
        # Add a Manager to each related Model.
        for attr_name, attr_value in related_fields:
            setattr(attr_value.related_model, attr_value.related_field, RelatedManager(new_class))
         
        return new_class


class BaseField:
    
    def __init__(self, required=True, unique=False, default=None):
        self.value = None
        self.name = None
        self.required = required
        self.unique = unique
        self.default = default

    def is_valid(self, value):
        """Return True if the provided value match the internal field."""
        if value is not None and not isinstance(value, self.internal_type):
            raise TypeError(
                "Type of field '{field_name}' must be an instance of {internal_type}.".format(
                    field_name=self.name, 
                    internal_type=self.internal_type))

        return True


class Field(BaseField): 
    internal_type = None
    sqlite_datatype = None

    def __get__(self, instance, owner):
        """
        Default getter of a Field subclass.
        
        If a field is accessed through a model instance, the value of the field for this particular
        instance is returned. Insted, if a field is accessed through the model class, the Field subclass
        is returned.
        """
        if instance is not None:
            return instance._values[self.name]
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
            instance._values[self.name] = value

    def sql(self):
        field_definition = [self.name, self.sqlite_datatype]
        
        if self.unique:
            field_definition.append(SQLiteAPI.UNIQUE)
        
        if self.required:
            field_definition.append(SQLiteAPI.NOT_NULL)
        
        if self.default is not None:
            field_definition.extend((SQLiteAPI.DEFAULT, str(self.default)))

        return field_definition
    

class TextField(Field):
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


class NumericField(Field):
    
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
    internal_type = int    
    sqlite_datatype = SQLiteAPI.INTEGER


class FloatField(NumericField):
    internal_type = float
    sqlite_datatype = SQLiteAPI.REAL


class PrimaryKeyField(IntegerField): 
    def __init__(self, **kwargs):
       kwargs.update(required=False)
       super().__init__(**kwargs)
    
    def sql(self):
        return super().sql() + [SQLiteAPI.PK, SQLiteAPI.AUTOINCREMENT]

     
class ForeignKeyField(IntegerField):

    def __init__(self, related_model, related_field):
        super().__init__() 
        self.related_model = related_model
        self.related_field = related_field
        
    def __set__(self, instance, value):
        """Store the primary key of a valid related model instance."""
        if self.is_valid(value):
            instance._values[self.name] = value.pk

    def is_valid(self, value):
        if not isinstance(value, self.related_model):
            raise TypeError(
                '{value} is not an instance of {class_name}'.format(
                    value=str(value),
                    class_name=self.related_model.__name__))
        
        return super().is_valid(value.pk)

    
    def _to_sql(self):
        return super._to_sql() + 'REFERENCES' + self.related_model.__name__.lower()


class Model(metaclass=BaseModel):
   
    pk = PrimaryKeyField()

    def __init__(self, **kwargs):
        # Each value for the current instance is stored in a hidden dictionary.
        self._values = { fieldname: None for fieldname in self._fieldnames }
        
        for attr_name, attr_value in kwargs.items():
            if hasattr(self, attr_name):
                setattr(self, attr_name, attr_value)
            else:
                raise AttributeError('<{}> model has no field "{}".'.format(self.__class__.__name__, attr_name))

        for fieldname, value in self._values.items():
            if getattr(self.__class__, fieldname).required and value is None:
                raise AttributeError('<{}> "{}" field is required: you need to provide a value.'.format(self.__class__.__name__, fieldname))
    
    def save(self):
        if self.pk is None:
            values = {field: value for field, value in self._values.items() if field != 'pk'}
            self.__class__.objects.create(**values)
        else:
            self.__class__.objects.update(User.pk == self.pk, **self._values)
    
    def __str__(self):
        return "{model}<{values}>".format(
            model=self.__class__.__name__,
            values=str(self._values)[1:-1],
        )
        
    def __eq__(self, other):
        return (
            len(self._values) == len(other._values) and
            all(other._values[field] == value for field, value in self._values.items())
        )


class Database:

    def __init__(self, db_name):
        self.db_name = db_name
        self._connection = sqlite3.connect(self.db_name)
   
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

