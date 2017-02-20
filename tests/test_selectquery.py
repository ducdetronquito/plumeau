from plume import *
from plume.plume import InsertQuery, SelectQuery
from utils import BaseTestCase, Pokemon, Trainer

import pytest

class TestSelectQueryAPI(BaseTestCase):

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            SelectQuery(self.db).__dict__

    def test_attributes(self):
        expected = (
            '_db', '_distinct', '_fields', '_limit', '_model',
            '_offset', '_order_by', '_tables'
        )
        result = SelectQuery(self.db).__slots__
        assert result == expected

    def test_is_filterable(self):
        assert hasattr(SelectQuery(self.db), 'where') is True

    def test_can_select_fields(self):
        assert hasattr(SelectQuery(self.db), 'select') is True

    def test_can_select_distinct(self):
        assert hasattr(SelectQuery(self.db), 'distinct') is True

    def test_can_select_fields_as_model_fields(self):
        query = SelectQuery(self.db).select(Trainer.name, Trainer.age).tables(Trainer).build()
        expected = 'SELECT trainer.name, trainer.age FROM trainer'
        assert query == expected

    def test_has_limit_method(self):
        assert hasattr(SelectQuery(self.db), 'limit') is True

    def test_has_offset_method(self):
        assert hasattr(SelectQuery(self.db), 'offset') is True

    def test_has_order_by_method(self):
        assert hasattr(SelectQuery(self.db), 'order_by') is True

    def test_can_be_iterated(self):
        assert hasattr(SelectQuery(self.db), '__iter__') is True

    def test_iter_return_a_list_of_model_instances(self):
        result = list(SelectQuery(self.db).tables(Trainer))
        for element in result:
            assert isinstance(element, Trainer) is True

    def test_can_be_accessed_by_index(self):
        assert hasattr(SelectQuery(self.db), '__getitem__') is True

    def test_can_return_result_as_list_of_dicts(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(self.db).tables(Trainer).dicts()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, dict) is True

    def test_can_select_fields_when_returning_dicts(self):
        self.add_trainer(['Giovanni'])
        result = SelectQuery(self.db).select(Trainer.name).tables(Trainer).dicts()
        assert len(result) == 1
        expected_dict = result[0]
        assert len(expected_dict.keys()) == 1
        assert 'name' in expected_dict
        assert expected_dict['name'] == 'Giovanni'

    def test_can_return_result_as_a_list_of_model_instances(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(self.db).tables(Trainer).get()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, Trainer) is True

    def test_fail_to_select_fields_when_returning_model_instances(self):
        self.add_trainer(['Giovanni'])
        with pytest.raises(AttributeError):
            result = SelectQuery(self.db).select(Trainer.name).tables(Trainer).get()

    def test_can_return_result_as_a_list_of_tuples(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(self.db).tables(Trainer).execute()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, tuple) is True

    def test_can_select_fields_when_returning_tuples(self):
        self.add_trainer(['Giovanni'])
        result = SelectQuery(self.db).select(Trainer.name).tables(Trainer).execute()
        assert len(result) == 1
        expected_tuple = result[0]
        assert len(expected_tuple) == 1
        assert 'Giovanni' in expected_tuple[0]

    def test_can_output_selectquery_as_string(self):
        query = SelectQuery(self.db).tables(Trainer).where(Trainer.age > 18)
        expected = "(SELECT * FROM trainer WHERE trainer.age > 18)"
        assert str(query) == expected

    def test_can_ouput_exists_expression(self):
        expression = SelectQuery(self.db).tables(Trainer).exists()
        expected = 'EXISTS (SELECT * FROM trainer)'
        assert str(expression) == expected


class TestSelectQueryLimitMethod(BaseTestCase):
    """Test behavior of a SelectQuery with the limit method."""
    def test_indexed_access_to_first_element_returns_a_model_instance(self):
        self.add_trainer('Giovanni')
        trainer = SelectQuery(db=self.db).tables(Trainer)[0]
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42

    def test_indexed_access_to_random_element_returns_a_model_instance(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainer = SelectQuery(db=self.db).tables(Trainer)[2]
        assert trainer.name == 'Jessie'
        assert trainer.age == 17

    def test_slice_access_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_slice_access_with_offset_only_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[:2]
        assert len(trainers) == 2
        assert trainers[0].name == 'Giovanni'
        assert trainers[0].age == 42
        assert trainers[1].name == 'James'
        assert trainers[1].age == 21


class TestSelectQueryLimitMethodeByIndex(BaseTestCase):
    """Test behavior of a SelectQuery with the limit shortcut."""

    def test_limit_to_a_single_element_return_model_instance(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainer = SelectQuery(db=self.db).tables(Trainer)[2]
        assert trainer.name == 'Jessie'
        assert trainer.age == 17

    def test_limit_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_limit_with_offset_only_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[1:]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_limit_with_offset_only_returns_a_pokemon_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(db=self.db).tables(Trainer)[:2]
        assert len(trainers) == 2
        assert trainers[0].name == 'Giovanni'
        assert trainers[0].age == 42
        assert trainers[1].name == 'James'
        assert trainers[1].age == 21


class TestSelectQueryWhere(BaseTestCase):

    def test_select_all_row(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).get()
        assert len(result) == 3
        giovanni, james, jessie = result
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        assert james.name == 'James'
        assert james.age == 21
        assert jessie.name == 'Jessie'
        assert jessie.age == 17

    def test_select_with_one_filter(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).where(Trainer.age > 18).get()
        assert len(result) == 2
        giovanni, james = result
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        assert james.name == 'James'
        assert james.age == 21

    def test_filter_with_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        giovanni_age = SelectQuery(db=self.db).tables(Trainer).select(Trainer.age).where(Trainer.name == 'Giovanni')
        result = SelectQuery(db=self.db).tables(Trainer).where(Trainer.age < giovanni_age).get()
        assert len(result) == 2
        james, jessie = result
        assert james.name == 'James'
        assert james.age == 21
        assert jessie.name == 'Jessie'
        assert jessie.age == 17

    def test_filter_with_AND_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).where((Trainer.age > 18)  & (Trainer.name != 'Giovanni')).get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filter_with_parameters_as_implicit_AND_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).where(Trainer.age > 18, Trainer.name != 'Giovanni').get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filters_can_be_chained(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        selectquery = SelectQuery(db=self.db).tables(Trainer).where(Trainer.age > 18)
        result = selectquery.where(Trainer.name != 'Giovanni').get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filter_with_IN_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).where(Trainer.age >> [17, 21]).get()
        assert len(result) == 2
        james, jessie = result
        assert james.name == 'James'
        assert james.age == 21
        assert jessie.name == 'Jessie'
        assert jessie.age == 17

    def test_IN_operator_filter_with_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        trainer_pks = SelectQuery(db=self.db).tables(Trainer).select(Trainer.pk).where(Trainer.name != 'Jessie')
        result = SelectQuery(db=self.db).tables(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> trainer_pks).execute()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'

    def test_IN_operator_filter_with_list_of_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        giovanni_pk = SelectQuery(db=self.db).tables(Trainer).select(Trainer.pk).where(Trainer.name == 'Giovanni')
        james_pk = SelectQuery(db=self.db).tables(Trainer).select(Trainer.pk).where(Trainer.name == 'James')
        result = SelectQuery(db=self.db).tables(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> [giovanni_pk, james_pk]).execute()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'

    def test_IN_operator_filter_with_list_of_value_and_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        giovanni_pk = SelectQuery(db=self.db).tables(Trainer).select(Trainer.pk).where(Trainer.name == 'Giovanni')
        james_pk = 2
        result = SelectQuery(db=self.db).tables(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> [giovanni_pk, james_pk]).execute()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'

    def test_filter_with_field_restriction_and_tuples_output(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(db=self.db).tables(Trainer).select(Trainer.name).where(Trainer.age >> [17, 21]).execute()
        assert len(result) == 2
        james, jessie = result
        print(result)
        assert len(james) == 1
        assert james[0] == 'James'
        assert len(jessie) == 1
        assert jessie[0] == 'Jessie'

    def test_filter_on_table_with_related_field(self):
        self.add_trainer('Giovanni')
        self.add_pokemon('Kangaskhan')
        result = SelectQuery(db=self.db).tables(Pokemon).get()
        assert len(result) == 1
        pokemon = result[0]
        assert pokemon.name == 'Kangaskhan'
        assert pokemon.level == 29
        assert isinstance(result[0].trainer, Trainer) is True
        trainer = pokemon.trainer
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42

    def test_can_select_distinct(self):
        query = SelectQuery(db=self.db).tables(Trainer).distinct(Trainer.name)
        expected = '(SELECT DISTINCT trainer.name FROM trainer)'
        assert str(query) == expected

    def test_result_select_distinct(self):
        self.add_trainer(['Giovanni', 'Giovanni'])
        ntrainers = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni'"
        ).fetchone()
        assert ntrainers[0] == 2

        result = SelectQuery(db=self.db).tables(Trainer).distinct(Trainer.name).execute()
        assert len(result) == 1

    def test_can_select_with_exists_return_false(self):
        result = SelectQuery(self.db).select(
            SelectQuery(self.db).tables(Trainer).exists()
        ).execute()
        expected = 0
        assert result[0][0] == expected

    def test_can_select_with_exists_return_true(self):
        InsertQuery(self.db).table(Trainer).from_dicts({
            'name': 'Giovanni',
            'age': 42
        }).execute()

        result = SelectQuery(self.db).select(
            SelectQuery(self.db).tables(Trainer).exists()
        ).execute()
        expected = 1
        assert result[0][0] == expected


class TestSelectQueryOrderBy(BaseTestCase):

    def test_can_order_by_one_field(self):
        query = SelectQuery(self.db).tables(Trainer).order_by(Trainer.name).build()
        expected = 'SELECT * FROM trainer ORDER BY trainer.name'
        assert query == expected

    def test_result_order_by_one_field(self):
        self.add_trainer(['Giovanni', 'Jessie'])
        result = (
            SelectQuery(self.db).select(Trainer.name).tables(Trainer)
            .order_by(Trainer.name).execute()
        )
        assert result[0][0] == 'Giovanni'
        assert result[1][0] == 'Jessie'

    def test_can_order_by_one_field_as_string(self):
        query = SelectQuery(self.db).tables(Trainer).order_by('name').build()
        expected = 'SELECT * FROM trainer ORDER BY name'
        assert query == expected

    def test_result_order_by_one_field_as_string(self):
        self.add_trainer(['Giovanni', 'Jessie'])
        result = (
            SelectQuery(self.db).select(Trainer.name).tables(Trainer)
            .order_by('name').execute()
        )
        assert result[0][0] == 'Giovanni'
        assert result[1][0] == 'Jessie'

    def test_can_order_by_one_field_with_sort_order_asc(self):
        query = SelectQuery(self.db).tables(Trainer).order_by(Trainer.name.asc()).build()
        expected = 'SELECT * FROM trainer ORDER BY trainer.name ASC'
        assert query == expected

    def test_result_order_by_one_field_with_sort_order_asc(self):
        self.add_trainer(['Giovanni', 'Jessie'])
        result = (
            SelectQuery(self.db).select(Trainer.name).tables(Trainer)
            .order_by(Trainer.name).execute()
        )
        assert result[0][0] == 'Giovanni'
        assert result[1][0] == 'Jessie'

    def test_can_order_by_one_field_with_sort_order_desc(self):
        query = SelectQuery(self.db).tables(Trainer).order_by(Trainer.name.desc()).build()
        expected = 'SELECT * FROM trainer ORDER BY trainer.name DESC'
        assert query == expected

    def test_result_order_by_one_field_with_sort_order_desc(self):
        self.add_trainer(['Giovanni', 'Jessie'])
        result = (
            SelectQuery(self.db).select(Trainer.name).tables(Trainer)
            .order_by(Trainer.name.desc()).execute()
        )
        assert result[0][0] == 'Jessie'
        assert result[1][0] == 'Giovanni'

    def test_can_order_by_several_fields(self):
        query = SelectQuery(self.db).tables(Trainer).order_by(Trainer.name, Trainer.age).build()
        expected = 'SELECT * FROM trainer ORDER BY trainer.name, trainer.age'
        assert query == expected

    def test_result_order_by_several_fields(self):
        InsertQuery(self.db).table(Trainer).from_dicts([
            {'name': 'Jessie', 'age': 17},
            {'name': 'Giovanni', 'age': 66},
            {'name': 'Giovanni', 'age': 42}
        ]).execute()

        result = (
            SelectQuery(self.db).select(Trainer.name, Trainer.age).tables(Trainer)
            .order_by(Trainer.name, Trainer.age).execute()
        )
        assert result == [('Giovanni', 42), ('Giovanni', 66), ('Jessie', 17)]

    def test_can_order_by_several_fields_with_sort_order(self):
        query = SelectQuery(self.db).tables(Trainer).order_by(
            Trainer.name.asc(), Trainer.age.desc()
        ).build()
        expected = 'SELECT * FROM trainer ORDER BY trainer.name ASC, trainer.age DESC'
        assert query == expected

    def test_result_order_by_several_fields_with_sort_order(self):
        InsertQuery(self.db).table(Trainer).from_dicts([
            {'name': 'Jessie', 'age': 17},
            {'name': 'Giovanni', 'age': 66},
            {'name': 'Giovanni', 'age': 42}
        ]).execute()

        result = (
            SelectQuery(self.db).select(Trainer.name, Trainer.age).tables(Trainer)
            .order_by(Trainer.name.asc(), Trainer.age.desc()).execute()
        )
        assert result == [('Giovanni', 66), ('Giovanni', 42), ('Jessie', 17)]
