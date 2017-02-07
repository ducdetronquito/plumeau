from plume import *
from plume.plume import SelectQuery
from utils import BaseTestCase, Pokemon, Trainer

import pytest

class TestSelectQueryAPI(BaseTestCase):

    def test_is_slotted(self):
        with pytest.raises(AttributeError):
            SelectQuery(Trainer).__dict__

    def test_attributes(self):
        expected = ('_count', '_distinct', '_fields', '_model', '_offset', '_tables')
        result = SelectQuery(Trainer).__slots__
        assert result == expected

    def test_is_filterable(self):
        assert hasattr(SelectQuery(Trainer), 'where') is True

    def test_can_select_fields(self):
        assert hasattr(SelectQuery(Trainer), 'select') is True
        
    def test_can_select_distinct(self):
        assert hasattr(SelectQuery(Trainer), 'distinct') is True

    def test_can_select_fields_as_model_fields(self):
        query = SelectQuery(Trainer)
        query.select(Trainer.name, Trainer.age).get()

    def test_can_be_limited(self):
        assert hasattr(SelectQuery(Trainer), 'limit') is True

    def test_fails_if_limit_and_offset_are_not_provided_when_limiting(self):
        with pytest.raises(TypeError):
            SelectQuery(Trainer).limit(limit=10)

    def test_can_be_iterated(self):
        assert hasattr(SelectQuery(Trainer), '__iter__') is True

    def test_iter_return_a_list_of_model_instances(self):
        result = list(SelectQuery(Trainer))
        for element in result:
            assert isinstance(element, Trainer) is True

    def test_can_be_accessed_by_index(self):
        assert hasattr(SelectQuery(Trainer), '__getitem__') is True

    def test_can_return_result_as_list_of_dicts(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).dicts()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, dict) is True

    def test_can_select_fields_when_returning_dicts(self):
        self.add_trainer(['Giovanni'])
        result = SelectQuery(Trainer).select(Trainer.name).dicts()
        assert len(result) == 1
        expected_dict = result[0]
        assert len(expected_dict.keys()) == 1
        assert 'name' in expected_dict
        assert expected_dict['name'] == 'Giovanni'

    def test_can_return_result_as_a_list_of_model_instances(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).get()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, Trainer) is True

    def test_fail_to_select_fields_when_returning_model_instances(self):
        self.add_trainer(['Giovanni'])
        with pytest.raises(AttributeError):
            result = SelectQuery(Trainer).select(Trainer.name).get()

    def test_can_return_result_as_a_list_of_tuples(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).tuples()
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, tuple) is True

    def test_can_select_fields_when_returning_tuples(self):
        self.add_trainer(['Giovanni'])
        result = SelectQuery(Trainer).select(Trainer.name).tuples()
        assert len(result) == 1
        expected_tuple = result[0]
        assert len(expected_tuple) == 1
        assert 'Giovanni' in expected_tuple[0]

    def test_can_return_result_as_a_list_of_namedtuples(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).tuples(named=True)
        assert isinstance(result, list) is True
        assert len(result) == 3
        for element in result:
            assert isinstance(element, tuple) is True
            assert hasattr(element, 'pk') is True
            assert hasattr(element, 'name') is True
            assert hasattr(element, 'age') is True

    def test_can_select_fields_when_returning_namedtuples(self):
        self.add_trainer(['Giovanni'])
        result = SelectQuery(Trainer).select(Trainer.name).tuples(named=True)
        assert len(result) == 1
        expected_namedtuple = result[0]
        assert len(expected_namedtuple) == 1
        assert expected_namedtuple.name == 'Giovanni'

    def test_can_output_selectquery_as_string(self):
        result = str(SelectQuery(Trainer).where(Trainer.age > 18))
        expected = "(SELECT * FROM trainer WHERE trainer.age > 18)"
        assert result == expected


class TestSelectQueryLimitMethod(BaseTestCase):
    """Test behavior of a SelectQuery with the limit method."""
    def test_indexed_access_to_first_element_returns_a_model_instance(self):
        self.add_trainer('Giovanni')
        trainer = SelectQuery(Trainer)[0]
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42

    def test_indexed_access_to_random_element_returns_a_model_instance(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainer = SelectQuery(Trainer)[2]
        assert trainer.name == 'Jessie'
        assert trainer.age == 17

    def test_slice_access_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_slice_access_with_offset_only_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_slice_access_with_offset_only_returns_a_pokemon_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[:2]
        assert len(trainers) == 2
        assert trainers[0].name == 'Giovanni'
        assert trainers[0].age == 42
        assert trainers[1].name == 'James'
        assert trainers[1].age == 21


class TestSelectQueryLimitMethodeByIndex(BaseTestCase):
    """Test behavior of a SelectQuery with the limit shortcut."""

    def test_limit_to_a_single_element_return_model_instance(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainer = SelectQuery(Trainer)[2]
        assert trainer.name == 'Jessie'
        assert trainer.age == 17

    def test_limit_with_start_and_stop_value_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[1:3]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_limit_with_offset_only_returns_a_model_instance_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[1:]
        assert len(trainers) == 2
        assert trainers[0].name == 'James'
        assert trainers[0].age == 21
        assert trainers[1].name == 'Jessie'
        assert trainers[1].age == 17

    def test_limit_with_offset_only_returns_a_pokemon_list(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        trainers = SelectQuery(Trainer)[:2]
        assert len(trainers) == 2
        assert trainers[0].name == 'Giovanni'
        assert trainers[0].age == 42
        assert trainers[1].name == 'James'
        assert trainers[1].age == 21


class TestSelectQueryWhere(BaseTestCase):

    def test_select_all_row(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).get()
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
        result = SelectQuery(Trainer).where(Trainer.age > 18).get()
        assert len(result) == 2
        giovanni, james = result
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        assert james.name == 'James'
        assert james.age == 21
        
    def test_filter_with_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        giovanni_age = SelectQuery(Trainer).select(Trainer.age).where(Trainer.name == 'Giovanni')
        result = SelectQuery(Trainer).where(Trainer.age < giovanni_age).get()
        assert len(result) == 2
        james, jessie = result
        assert james.name == 'James'
        assert james.age == 21
        assert jessie.name == 'Jessie'
        assert jessie.age == 17

    def test_filter_with_AND_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).where((Trainer.age > 18)  & (Trainer.name != 'Giovanni')).get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filter_with_parameters_as_implicit_AND_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).where(Trainer.age > 18, Trainer.name != 'Giovanni').get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filters_can_be_chained(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        selectquery = SelectQuery(Trainer).where(Trainer.age > 18)
        result = selectquery.where(Trainer.name != 'Giovanni').get()
        assert len(result) == 1
        james = result[0]
        assert james.name == 'James'
        assert james.age == 21

    def test_filter_with_IN_operator(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).where(Trainer.age >> [17, 21]).get()
        assert len(result) == 2
        james, jessie = result
        assert james.name == 'James'
        assert james.age == 21
        assert jessie.name == 'Jessie'
        assert jessie.age == 17
        
    def test_IN_operator_filter_with_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        trainer_pks = SelectQuery(Trainer).select(Trainer.pk).where(Trainer.name != 'Jessie')
        result = SelectQuery(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> trainer_pks).tuples()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'
        
    def test_IN_operator_filter_with_list_of_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        giovanni_pk = SelectQuery(Trainer).select(Trainer.pk).where(Trainer.name == 'Giovanni')
        james_pk = SelectQuery(Trainer).select(Trainer.pk).where(Trainer.name == 'James')
        result = SelectQuery(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> [giovanni_pk, james_pk]).tuples()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'
        
    def test_IN_operator_filter_with_list_of_value_and_query(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        self.add_pokemon(['Kangaskhan', 'Koffing', 'Wobbuffet'])
        giovanni_pk = SelectQuery(Trainer).select(Trainer.pk).where(Trainer.name == 'Giovanni')
        james_pk = 2
        result = SelectQuery(Pokemon).select(Pokemon.name).where(Pokemon.trainer >> [giovanni_pk, james_pk]).tuples()
        assert len(result) == 2
        assert result[0][0] == 'Kangaskhan'
        assert result[1][0] == 'Koffing'

    def test_filter_with_field_restriction_and_tuples_output(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = SelectQuery(Trainer).select(Trainer.name).where(Trainer.age >> [17, 21]).tuples()
        assert len(result) == 2
        james, jessie = result
        print(result)
        assert len(james) == 1
        assert james[0] == 'James'
        assert len(jessie) == 1
        assert jessie[0] == 'Jessie'

    def test_filter_with_field_restriction_and_namedtuples_output(self):
        self.add_trainer(['Giovanni', 'James', 'Jessie'])
        result = (
            Trainer.select(Trainer.name)
                   .where(Trainer.age >> [17, 21])
                   .tuples(named=True)
        )
        assert len(result) == 2
        james, jessie = result
        print(james)
        print(result)
        assert len(james) == 1
        assert james.name == 'James'
        assert len(jessie) == 1
        assert jessie.name == 'Jessie'

    def test_filter_on_table_with_related_field(self):
        self.add_trainer('Giovanni')
        self.add_pokemon('Kangaskhan')
        result = SelectQuery(Pokemon).get()
        assert len(result) == 1
        pokemon = result[0]
        assert pokemon.name == 'Kangaskhan'
        assert pokemon.level == 29
        assert isinstance(result[0].trainer, Trainer) is True
        trainer = pokemon.trainer
        assert trainer.name == 'Giovanni'
        assert trainer.age == 42
        
    def test_can_select_distinct(self):
        query = SelectQuery(Trainer).distinct(Trainer.name)
        expected = '(SELECT DISTINCT trainer.name FROM trainer)'
        assert str(query) == expected

    def test_can_filter_duplicates(self):
        self.add_trainer(['Giovanni', 'Giovanni'])
        ntrainers = Trainer._db._connection.execute(
            "SELECT count(name) FROM trainer WHERE name = 'Giovanni'"
        ).fetchone()
        assert ntrainers[0] == 2
        
        result = SelectQuery(Trainer).distinct(Trainer.name).tuples()
        assert len(result) == 1
        

