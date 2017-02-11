from plume.plume import DeleteQuery, Model, SelectQuery, SQLiteDB, UpdateQuery

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

    def test_has_update_method(self):
        assert hasattr(Trainer, 'update') is True
         
    def test_has_delete_method(self):
        assert hasattr(Trainer, 'delete') is True
    
    def test_has_select_method(self):
        assert hasattr(Trainer, 'select') is True
        
    def test_has_where_method(self):
        assert hasattr(Trainer, 'where') is True
        

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
        meowth = Pokemon.create(name='Meowth', level=19, trainer=james.pk)
        
        assert james.pk == 1
        assert meowth.trainer.pk == james.pk
        
    def test_create_checks_for_integrity(self):
        james = Trainer.create(name='James', age=21)

        with pytest.raises(sqlite3.IntegrityError):
            Pokemon.create(name='Meowth', level=19, trainer=2)

    def test_create_many(self):
        ntrainers = Trainer._db._connection.execute(
            "SELECT count(*) FROM trainer WHERE name = 'Giovanni' OR name = 'James'"
        ).fetchone()
        
        assert ntrainers[0] == 0
        
        Trainer.create_many([
            {'name': 'Giovanni', 'age': 42},
            {'name': 'James', 'age': 21}
        ])
        
        trainers = Trainer._db._connection.execute(
            "SELECT name, age FROM trainer WHERE name = 'Giovanni' OR name = 'James'"
        ).fetchall()
        
        assert trainers[0][0] == 'Giovanni'
        assert trainers[0][1] == 42
        assert trainers[1][0] == 'James'
        assert trainers[1][1] == 21


            
        
        


