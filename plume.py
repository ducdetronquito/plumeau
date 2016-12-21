from collections import deque
from contextlib import closing
from copy import deepcopy
import sqlite3

"""
To do:
    - Add "in" query operator (>> or tune ==)
    - Handle ORDER BY
    - Add tests all classes
    - Comply to PEP8 and Google Python Style Guide as much as possible.
    - Handle Foreign Keys T_T
"""

class SQLiteAPI:
    
    AND = ' AND '
    OR = ' OR '
    SELECT = 'SELECT '
    FROM = ' FROM '
    WHERE = ' WHERE '
    LIMIT = ' LIMIT '
    OFFSET = ' OFFSET '
    
    @classmethod
    def select(cls, params):
        query = []
        
        query.extend((
            SQLiteAPI.SELECT, SQLiteAPI.to_csv(params.get('fields', '*')),
        ))
        
        if 'tables' in params:
            query.extend((
                SQLiteAPI.FROM, SQLiteAPI.to_csv(params['tables']),
            ))
        
        if 'where' in params:
            query.extend((
                SQLiteAPI.WHERE, ''.join(params['where']),
            ))
            
        if 'limit' in params:
            query.extend((
                SQLiteAPI.LIMIT, str(params['limit'][0]), SQLiteAPI.OFFSET, str(params['limit'][1]),
            ))
        
        return ''.join(query)

    @staticmethod
    def to_csv(values):
        """Convert a string value or a sequence of string values into a coma-separated string."""
        try:
            return values.lower()
        except AttributeError:
            return ', '.join((v.lower() for v in values))
            

class Clause(deque):
    
    def __init__(self, value):
        self.append(value)
    
    def __and__(self, other):
        self.appendleft(''.join((str(other), SQLiteAPI.AND)))
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
        self._criteria = []

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
        self._criteria.extend(args)
        
        return self
        
    def __execute_query(self, query):
        """Query the database and returns the result as a list of model instances."""
        return iter([
            self._model(**{
                fieldname: value for fieldname, value in zip(self._model._fieldnames, instance)
            })
            for instance in self._model._db.select(query)
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
        params = {
            'tables': self._model.__name__.lower(),
        }
        
        if self._criteria:
            params['where'] = (str(criterion) for criterion in self._criteria)
    
        return self.__execute_query(SQLiteAPI.select(params))
    
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
        
        params = {
            'tables': self._model.__name__.lower(),
            'limit': (count, offset),
        }
        
        if self._criteria:
            params['where'] = (str(criterion) for criterion in self._criteria)
            
        result = self.__execute_query(SQLiteAPI.select(params))
        
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
        values = [(fieldname, kwargs[fieldname]) for fieldname in self._model._fieldnames if fieldname in kwargs]
        query = 'INSERT INTO {table_name}({fieldnames}) VALUES ({placeholders})'.format(
            table_name=self._model.__name__.lower(),
            fieldnames=', '.join([value[0] for value in values]),
            placeholders=('?,'*len(values))[:-1]
        )
        vals = tuple([value[1] for value in values])
        
        last_row_id = self._model._db.insert_into(query, vals)
        values.append(('pk',  last_row_id))
        kwargs =  {field: value for field, value in values}
        
        return self._model(**kwargs) 

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
    
    def __init__(self, required=True, unique=False):
        self.value = None
        self.name = None
        self.required = required
        self.unique = unique

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

    def _to_sql(self):
        return ' '.join([
            self.name,
            self.sqlite_datatype,
            'UNIQUE' if self.unique else '',
            'NOT NULL' if self.required else '',
        ])


class TextField(Field):
    internal_type = str
    sqlite_datatype = 'TEXT'
    
    def __eq__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '=', ''.join(("'", other, "'")))

    def __ne__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '!=', ''.join(("'", other, "'")))


class NumericField(Field):
    
    def __eq__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '=', other)

    def __ne__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '!=', other)

    def __lt__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '<', other)

    def __le__(self, other):
        if self.is_valid(other): 
            return Criterion(self.name, '<=', other)

    def __gt__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '>', other)

    def __ge__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '>=', other)


class IntegerField(NumericField):
    internal_type = int    
    sqlite_datatype = 'INTEGER' 


class FloatField(NumericField):
    internal_type = float
    sqlite_datatype = 'REAL'


class PrimaryKeyField(IntegerField): 
    def __init__(self, **kwargs):
       kwargs.update(required=False)
       super().__init__(**kwargs)
    
    def _to_sql(self):
        return super()._to_sql() + 'PRIMARY KEY AUTOINCREMENT'

     
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
    
    def select(self, query):
        with closing(self._connection.cursor()) as cursor:
            return cursor.execute(query).fetchall()

    def create_table(self, model_class):
         
        fields = [
            getattr(model_class, fieldname)._to_sql()
            for fieldname in model_class._fieldnames
        ]

        query = 'CREATE TABLE IF NOT EXISTS {table_name} ({columns})'.format(
            table_name=model_class.__name__.lower(),
            columns=', '.join(fields)
        )

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


