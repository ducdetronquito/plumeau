from plume.plume import Database, DeleteQuery, Model, SelectQuery, UpdateQuery

from utils import BaseTestCase, Pokemon, Trainer

import pytest
import sqlite3

class TestModelAPI:
    
    def test_custom_model_is_sloted(self):
        sacha = Trainer(name='Sacha', age=42)
        
        with pytest.raises(AttributeError):
            sacha.__dict__
        
    def test_fieldnames_class_attribute_contains_primary_key_field_name(self):
        assert len(Model._fieldnames) == 1
        assert 'pk' in Model._fieldnames
        
    def test_pk_field_is_empty_by_default_on_model_instance(self):
        assert Model().pk is None
    
    def test_pk_field_can_be_set_as_model_instance_init_param(self):
        m = Model(pk=1)
        assert Model.pk == 1

    def test_two_models_with_same_pk_are_equals(self):
        m1 = Model(pk=1)
        m2 = Model(pk=1)
        assert m1 == m2
        
    def test_two_models_with_differents_pk_are_not_equals(self):
        m1 = Model(pk=1)
        m2 = Model(pk=2)
        assert m1 != m2

    def test_can_make_update_query(self):
        query = Trainer.update(Trainer.age == 42)
        expected = '(UPDATE trainer SET age = 42)'
        assert isinstance(query, UpdateQuery) is True
        assert str(query) == expected
    
    def test_can_make_delete_query(self):
        query = Trainer.delete(Trainer.age == 42)
        expected = '(DELETE FROM trainer WHERE trainer.age = 42)'
        assert isinstance(query, DeleteQuery) is True
        assert str(query) == expected
    
    def test_can_make_select_query_with_select(self):
        query = Trainer.select(Trainer.age)
        expected = '(SELECT trainer.age FROM trainer)'
        assert isinstance(query, SelectQuery) is True
        assert str(query) == expected
        
    def test_can_make_select_query_with_where(self):
        query = Trainer.where(Trainer.age == 42)
        expected = '(SELECT * FROM trainer WHERE trainer.age = 42)'
        assert isinstance(query, SelectQuery) is True
        assert str(query) == expected
        

class TestModelResult(BaseTestCase):    
    def test_create_returns_an_instance_with_pk_set(self):
        giovanni = Trainer.create(name='Giovanni', age=42)
        assert giovanni.pk == 1
        assert giovanni.name == 'Giovanni'
        assert giovanni.age == 42
        
    def test_create_returns_an_instance_with_pk_set_to_next_available_id(self):
        giovanni = Trainer.create(name='Giovanni', age=42)
        james = Trainer.create(name='James', age=21)
        assert giovanni.pk == 1
        assert james.pk == 2

    def test_create_allows_model_instance_as_parameter_for_foreign_key_field(self):
        james = Trainer.create(name='James', age=21)
        meowth = Pokemon.create(name='Meowth', level=19, trainer=james)
        
        assert james.pk == 1
        assert meowth.trainer.pk == james.pk
        
    def test_create_checks_for_integrity(self):
        james = Trainer.create(name='James', age=21)
        
        with pytest.raises(sqlite3.IntegrityError):
            Pokemon.create(name='Meowth', level=19, trainer=2)
        
        


