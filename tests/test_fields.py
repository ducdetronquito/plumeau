from plume.plume import (
    Field, ForeignKeyField, FloatField, IntegerField,
    Model, PrimaryKeyField, SQLiteDB, TextField,
)
from utils import Attack, Pokemon, Trainer

import pytest


class TestField:

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            Field().__dict__

    def test_field_value_is_required_by_default(self):
        assert Field().required is True

    def test_field_value_is_not_unique_by_default(self):
        assert Field().unique is False

    def test_default_field_value_is_not_defined(self):
        assert Field().default is None

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

    class User(Model):
        field = FloatField()

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

    def test_default_value_needs_to_be_a_float(self):
        with pytest.raises(TypeError):
            field = FloatField(default=42)

    def test_allows_equal_operator(self):
        criterion = (self.User.field == 6.66)
        assert str(criterion) == "user.field = 6.66"

    def test_allows_not_equal_operator(self):
        criterion = (self.User.field != 6.66)
        assert str(criterion) == "user.field != 6.66"

    def test_allows_in_operator(self):
        criterion = (self.User.field >> [6.66, 42.0])
        assert str(criterion) == "user.field IN (6.66, 42.0)"

    def test_allows_lower_than_operator(self):
        criterion = (self.User.field < 6.66)
        assert str(criterion) == "user.field < 6.66"

    def test_allows_lower_than_equals_operator(self):
        criterion = (self.User.field <= 6.66)
        assert str(criterion) == "user.field <= 6.66"

    def test_allows_greater_than_operator(self):
        criterion = (self.User.field > 6.66)
        assert str(criterion) == "user.field > 6.66"

    def test_allows_greater_than_equals_operator(self):
        criterion = (self.User.field >= 6.66)
        assert str(criterion) == "user.field >= 6.66"

    def test_allows_between_operator(self):
        db = SQLiteDB(':memory:')
        db.register(Attack)
        expression = Attack.accuracy.between(6.66, 42.0)
        expected = 'attack.accuracy BETWEEN 6.66 AND 42.0'
        assert str(expression) == expected


class TestForeignKeyField:
    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            ForeignKeyField(Pokemon, 'pokemons').__dict__

    def test_store_pk_of_a_model_instance(self):
        db = SQLiteDB(':memory:')
        db.register(Trainer, Pokemon)
        james = Trainer.create(pk=1, name='James', age=21)
        meowth = Pokemon.create(name='Meowth', level=3, trainer=james.pk)
        assert meowth.trainer.pk == 1

    def test_for_create_table_query_sql_output_a_list_of_keywords(self):
        field = ForeignKeyField(Pokemon, 'pokemons')
        field.name = 'field'
        result = field.sql()
        expected = ['field', 'INTEGER', 'NOT NULL', 'REFERENCES', 'pokemon(pk)']
        assert result == expected


class TestIntegerField:

    class User(Model):
        field = IntegerField()

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

    def test_default_value_needs_to_be_an_integer(self):
        with pytest.raises(TypeError):
            field = IntegerField(default=6.66)

    def test_allows_equal_operator(self):
        criterion = (self.User.field == 42)
        assert str(criterion) == "user.field = 42"

    def test_allows_not_equal_operator(self):
        criterion = (self.User.field != 42)
        assert str(criterion) == "user.field != 42"

    def test_allows_in_operator(self):
        criterion = (self.User.field >> [42, 666])
        assert str(criterion) == "user.field IN (42, 666)"

    def test_allows_lower_than_operator(self):
        criterion = (self.User.field < 42)
        assert str(criterion) == "user.field < 42"

    def test_allows_lower_than_equals_operator(self):
        criterion = (self.User.field <= 42)
        assert str(criterion) == "user.field <= 42"

    def test_allows_greater_than_operator(self):
        criterion = (self.User.field > 42)
        assert str(criterion) == "user.field > 42"

    def test_allows_greater_than_equals_operator(self):
        criterion = (self.User.field >= 42)
        assert str(criterion) == "user.field >= 42"

    def test_allows_between_operator(self):
        db = SQLiteDB(':memory:')
        db.register(Trainer)
        expression = Trainer.age.between(17, 42)
        expected = 'trainer.age BETWEEN 17 AND 42'
        assert str(expression) == expected

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

    def test_default_value_needs_to_be_an_integer(self):
        with pytest.raises(TypeError):
            field = PrimaryKeyField(default=6.66)


class TestTextField:

    class User(Model):
        field = TextField()

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
        expected = ['field', 'TEXT', 'UNIQUE', 'NOT NULL', 'DEFAULT', "'empty'"]
        assert result == expected

    def test_default_value_needs_to_be_a_string(self):
        with pytest.raises(TypeError):
            field = TextField(default=42)

    def test_allows_equal_operator(self):
        criterion = (self.User.field == 'value')
        assert str(criterion) == "user.field = 'value'"

    def test_allows_not_equal_operator(self):
        criterion = (self.User.field != 'value')
        assert str(criterion) == "user.field != 'value'"

    def test_allows_in_operator(self):
        criterion = (self.User.field >> ['value1', 'value2'])
        print(str(criterion))
        assert str(criterion) == "user.field IN ('value1', 'value2')"

    def test_allows_between_operator(self):
        db = SQLiteDB(':memory:')
        db.register(Trainer)
        expression = Trainer.name.between('A', 'Z')
        expected = "trainer.name BETWEEN 'A' AND 'Z'"
        assert str(expression) == expected
