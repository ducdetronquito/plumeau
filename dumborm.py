from contextlib import closing
from copy import deepcopy
import sqlite3

"""
To do:
    - Make a proper test file
    - Refactor interface of Manager/QuerySet
    - Handle AND/OR filters
    - Handle ORDER BY
    - Handle Foreign Keys T_T
"""

# The Criterion should be evaluated in itself of by QuerySet ?
class Criterion:
    
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def evaluate(self):
        return ' '.join((self.field, self.operator, str(self.value)))

class QuerySet:
    
    def __init__(self, model):
        self._model = model
        self._criteria = []

    def filter(self, *args):
        self._criteria.extend(args)
        return self

    def __iter__(self): 
        criteria = ' AND '.join([criterion.evaluate() for criterion in self._criteria])
     
        query = 'SELECT {fields} FROM {table} WHERE {filters}'.format(
            fields='*',
            table=self._model.__name__.lower(),
            filters=criteria,
        )
        
        print(query)

        return iter([
            self._model(**{fieldname: value for fieldname, value in zip(self._model._fieldnames, instance)})
            for instance in self._model._db.select(query)
        ])

class Manager:

    def __init__(self, model):
        self._model = model
        self._queryset = None

    def __get__(self, instance, owner):
        """A Model Manager is only accessible as a class attribute."""
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
        print(query, '=>',vals)

        last_row_id = self._model._db.insert_into(query, vals)
        values.append(('pk',  last_row_id))
        kwargs =  {field: value for field, value in values}
        
        return self._model(**kwargs) 

    def select(self, *args):
        """Fetch related data an create model instance."""
        """
        args = ', '.join(args) or '*'
        query = 'SELECT {args} from {table}'.format(args=args, table=self._model.__name__.lower())
        print(query)
        
        return [
            self._model(**{fieldname: value for fieldname, value in zip(self._model._fieldnames, instance)})
            for instance in self._model._db.select(query)
        ]
        """
        return QuerySet(self._model)

    def update(self, criterion, **kwargs):
       raise NotImplementedError("Updating model is not available now") 

    def filter(self, *args):
        return QuerySet(self._model).filter(*args)

    def order_by(self, *args):
        self._queryset = self._queryset or QuerySet()
        
        return self._queryset.order_by(*args)


class RelatedManager(Manager):
    
    def __get__(self, instance, owner):
        """A RelatedManager is only accessible as an instance attribute."""
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

    def __eq__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '=', other)

    def __ne__(self, other):
        if self.is_valid(other):
            return Criterion(self.name, '<>', other)

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
        

class NumericField(Field):
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

class Database:

    def __init__(self, db_name):
        self.db_name = db_name
        self._connection = sqlite3.connect(self.db_name)
        
        #self._connection.execute('PRAGMA foreign_keys = ON')
   
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
        
        query = 'CREATE TABLE IF NOT EXISTS {table_name} ({columns})'
       
        fields = [
            getattr(model_class, fieldname)._to_sql()
            for fieldname in model_class._fieldnames
        ]

        query = query.format(
            table_name=model_class.__name__.lower(),
            columns=', '.join(fields)
        )
        
        print(query)

        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query) 
            self._connection.commit()
    
    def register(self, *args):
        for model_class in args:
            model_class._db = self
            
            try:
                self.create_table(model_class)
            except:
                raise TypeError('{arg} is not a valid Model subclass.'.format(arg=model_class.__name__))
