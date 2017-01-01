from plume.plume import (
    Criterion, Database, Field, ForeignKeyField, FloatField,
    IntegerField, Model, PrimaryKeyField, TextField,
)
from utils import DB_NAME, Pokemon, Trainer

import pytest


class TestField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Field().__dict__
            
    def test_field_value_is_required_by_default(self):
        a = Field()
        assert a.required is True
    
    def test_field_value_is_not_unique_by_default(self):
        a = Field()
        assert a.unique is False
    
    def test_default_field_value_is_not_defined(self):
        a = Field()
        assert a.default is None

    def test_class_access_returns_Field_class(self):
        class User(Model):
            field = Field()
        
        assert isinstance(User.field, Field) is True
    
    def test_instance_access_returns_field_value(self):
        class User(Model):
            field = Field()
        
        user = User(field='value')
        assert user.field == 'value'


class TestFloatField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            FloatField().__dict__
            
    def test_sqlite_type_is_REAL(self):
        assert FloatField.sqlite_datatype == 'REAL'
    
    def test_internal_type_is_str(self):
        assert FloatField.internal_type is float
        
    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = FloatField(required=True, unique=True, default=0.0)
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'REAL', 'UNIQUE', 'NOT NULL', 'DEFAULT', '0.0']
        assert result == expected
        
    def test_allows_equal_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field == 6.66)
        assert str(criterion) == "field = 6.66"
    
    def test_equal_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field == 42)
            
    def test_allows_not_equal_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field != 6.66)
        assert str(criterion) == "field != 6.66"
        
    def test_not_equal_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field != 42)
    
    def test_allows_in_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field << [6.66, 42.0])
        
        assert str(criterion) == "field IN (6.66, 42.0)"
    
    def test_in_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field << [6.66, 42])

    def test_allows_lower_than_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field < 6.66)
        assert str(criterion) == "field < 6.66"
    
    def test_lower_than_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field < 42)

    def test_allows_lower_than_equals_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field <= 6.66)
        assert str(criterion) == "field <= 6.66"
    
    def test_lower_than_equals_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field <= 42)

    def test_allows_greater_than_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field > 6.66)
        assert str(criterion) == "field > 6.66"
    
    def test_greater_than_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field > 42)
    
    def test_allows_greater_than_equals_operator(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field >= 6.66)
        assert str(criterion) == "field >= 6.66"
    
    def test_greater_than_equals_operator_raises_error_if_field_value_is_not_a_float(self):
        field = FloatField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field >= 42)


class TestForeignKeyField:
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            ForeignKeyField(Pokemon, 'pokemons').__dict__

    def test_store_pk_of_a_model_instance(self):
        db = Database(DB_NAME)
        db.register(Trainer, Pokemon)
        james = Trainer.objects.create(pk=1, name='James', age=21)
        meowth = Pokemon.objects.create(name='Meowth', level=3, trainer=james)
        assert meowth.trainer.pk == 1

    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = ForeignKeyField(Pokemon, 'pokemons')
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'INTEGER', 'NOT NULL', 'REFERENCES', 'pokemon(pk)']
        assert result == expected


class TestIntegerField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            IntegerField().__dict__

    def test_sqlite_type_is_REAL(self):
        assert IntegerField.sqlite_datatype == 'INTEGER'
    
    def test_internal_type_is_str(self):
        assert IntegerField.internal_type is int
        
    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = IntegerField(required=True, unique=True, default=0)
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'INTEGER', 'UNIQUE', 'NOT NULL', 'DEFAULT', '0']
        assert result == expected
        
    def test_allows_equal_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field == 42)
        assert str(criterion) == "field = 42"
    
    def test_equal_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field == 6.66)
            
    def test_allows_not_equal_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field != 42)
        assert str(criterion) == "field != 42"
        
    def test_not_equal_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field != 6.66)
    
    def test_allows_in_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field << [42, 666])
        
        assert str(criterion) == "field IN (42, 666)"
    
    def test_in_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field << [6.66, 42])

    def test_allows_lower_than_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field < 42)
        assert str(criterion) == "field < 42"
    
    def test_lower_than_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field < 6.66)

    def test_allows_lower_than_equals_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field <= 42)
        assert str(criterion) == "field <= 42"
    
    def test_lower_than_equals_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field <= 6.66)

    def test_allows_greater_than_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field > 42)
        assert str(criterion) == "field > 42"
    
    def test_greater_than_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field > 6.66)
    
    def test_allows_greater_than_equals_operator(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field >= 42)
        assert str(criterion) == "field >= 42"
    
    def test_greater_than_equals_operator_raises_error_if_field_value_is_not_a_integer(self):
        field = IntegerField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field >= 6.66)


class TestPrimaryKeyField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            PrimaryKeyField().__dict__

    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = PrimaryKeyField(unique=True, default=1)
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'INTEGER', 'UNIQUE', 'DEFAULT', '1', 'PRIMARY KEY', 'AUTOINCREMENT']
        assert result == expected
        
    def test_required_is_not_specified_in_sql_create_query_output(self):
        field = PrimaryKeyField(required=True)
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'INTEGER', 'PRIMARY KEY', 'AUTOINCREMENT']
        assert result == expected
        
    
class TestTextField:
    
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            TextField().__dict__
            
    def test_sqlite_type_is_TEXT(self):
        assert TextField.sqlite_datatype == 'TEXT'
    
    def test_internal_type_is_str(self):
        assert TextField.internal_type is str
        
    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = TextField(required=True, unique=True, default='empty')
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'TEXT', 'UNIQUE', 'NOT NULL', 'DEFAULT', 'empty']
        assert result == expected
        
    def test_allows_equal_operator(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field == 'value')
        assert str(criterion) == "field = 'value'"
    
    def test_equal_operator_raises_error_if_field_value_is_not_a_string(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field == 42)
            
    def test_allows_not_equal_operator(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field != 'value')
        assert str(criterion) == "field != 'value'"
        
    def test_not_equal_operator_raises_error_if_field_value_is_not_a_string(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field != 42)
    
    def test_allows_in_operator(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        criterion = (field << ['value1', 'value2'])
        
        assert str(criterion) == "field IN ('value1', 'value2')"
    
    def test_in_operator_raises_error_if_field_value_is_not_a_string(self):
        field = TextField()
        field.name = 'field' # Automatically done in BaseModel.
        with pytest.raises(TypeError):
            criterion = (field << ['value1', 42])
